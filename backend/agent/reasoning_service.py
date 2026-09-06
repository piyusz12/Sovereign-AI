"""
Reasoning model service (Qwen3-14B via Ollama), used by the Phase 11 agent
graph for the three jobs that need judgment rather than code generation:
understanding the goal, planning, and verifying results. Mirrors
backend/router/coder_service.py's shape deliberately — same provider
(Ollama), same swap point for LiteLLM/vLLM later.

Every function here returns parsed JSON. Small local models are not always
perfectly well-behaved about "JSON only," so responses are defensively
extracted and a clear error is raised on failure rather than silently
returning garbage into the agent state.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Any, List

import httpx

try:
    from backend.settings import settings
    OLLAMA_BASE_URL = getattr(settings, "ollama_base_url", "http://127.0.0.1:11434")
    REASONING_MODEL_NAME = getattr(settings, "ollama_reasoning_model", "qwen3:14b")
except Exception:
    OLLAMA_BASE_URL = "http://127.0.0.1:11434"
    REASONING_MODEL_NAME = "qwen3:14b"

DEFAULT_TIMEOUT_SECONDS = 120

# Only "coding" is actually wired to a real tool as of Phase 11. The other
# task types are recognized so the router demo (Phase 27) reads correctly,
# but they resolve to "unsupported" until Phases 12-19 (RAG) and Phase 19
# (vision) land.
KNOWN_TASK_TYPES = ["coding", "document_reasoning", "vision", "general_reasoning"]
IMPLEMENTED_TASK_TYPES = {"coding"}

logger = logging.getLogger("sovereign.agent.reasoning")


class ReasoningServiceError(RuntimeError):
    pass


@dataclass
class ClassificationResult:
    task_type: str
    reason: str


def _clean_markdown_fences(text: str) -> str:
    """Strip markdown code fence wrappers if present."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[len("```json"):].strip()
    elif text.startswith("```"):
        text = text[len("```"):].strip()
    if text.endswith("```"):
        text = text[:-len("```")].strip()
    return text


def _extract_json(text: str) -> dict[str, Any]:
    cleaned = _clean_markdown_fences(text)
    
    # Try parsing the whole string first
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
        
    # Fallback to regex isolation
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not match:
        raise ReasoningServiceError(f"No JSON object found in model output: {text[:300]}")
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise ReasoningServiceError(f"Malformed JSON from model: {exc}\n{text[:300]}") from exc


def _chat(system_prompt: str, user_prompt: str, *, timeout: float = DEFAULT_TIMEOUT_SECONDS, max_retries: int = 3) -> str:
    import time
    import asyncio
    from backend.models import route_task, RoutingRequest, TaskType
    from backend.model_gateway import model_gateway, GatewayInferenceRequest, ChatMessage
    
    last_error = None
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    for attempt in range(1, max_retries + 1):
        start_time = time.time()
        try:
            # Phase 27: Select the reasoning model dynamically
            route = route_task(RoutingRequest(task_type=TaskType.GENERAL_CHAT))
            # Since this function is sync and runs in a thread pool, we run the async code inline
            request = GatewayInferenceRequest(
                model=route.selected_model,
                messages=[ChatMessage(**m) for m in messages],
                temperature=0.1
            )
            response = asyncio.run(model_gateway.generate(request))
            content = response.content
            
            duration = (time.time() - start_time) * 1000
            
            if not content:
                raise ReasoningServiceError("Empty response from reasoning model.")
                
            logger.info("Reasoning inference (via %s) completed in %.2fms (attempt %d)", route.selected_model, duration, attempt)
            
            # Fast-fail JSON validation if system prompt requested JSON
            if "JSON" in system_prompt:
                # This will raise ReasoningServiceError if invalid
                _extract_json(content)
                
            return content
            
        except ReasoningServiceError as exc:
            last_error = exc
            logger.warning("Reasoning validation failed on attempt %d: %s", attempt, exc)
            if "content" in locals() and content:
                messages.append({"role": "assistant", "content": content})
            messages.append({
                "role": "user", 
                "content": f"Your last response failed JSON validation: {exc}. Output ONLY valid JSON."
            })
            
        except Exception as exc:
            raise ReasoningServiceError(f"Reasoning model request failed: {exc}") from exc
            
    raise ReasoningServiceError(f"Failed to get valid response after {max_retries} attempts. Last error: {last_error}")


def classify_task(user_request: str) -> ClassificationResult:
    """Phase 11 'Understand Goal' node. One of KNOWN_TASK_TYPES."""
    system_prompt = (
        "You classify a user's request into exactly one task_type: "
        f"{', '.join(KNOWN_TASK_TYPES)}.\n"
        "Respond with ONLY a JSON object: "
        '{"task_type": "...", "reason": "one short sentence"}. No prose, no markdown.'
    )
    content = _chat(system_prompt, user_request)
    data = _extract_json(content)
    task_type = data.get("task_type", "").strip()
    if task_type not in KNOWN_TASK_TYPES:
        task_type = "general_reasoning"
    return ClassificationResult(task_type=task_type, reason=data.get("reason", ""))


def make_plan(user_request: str, task_type: str) -> List[str]:
    """Phase 11 'Plan' node. Short, ordered, human-readable steps."""
    system_prompt = (
        "You write a short plan (2-5 steps) for how an AI agent should carry "
        "out the user's request. Respond with ONLY a JSON object: "
        '{"steps": ["step one", "step two", ...]}. No prose, no markdown.'
    )
    content = _chat(system_prompt, f"Task type: {task_type}\nRequest: {user_request}")
    data = _extract_json(content)
    steps = data.get("steps", [])
    if not isinstance(steps, list) or not steps:
        raise ReasoningServiceError(f"Plan response had no usable steps: {content[:300]}")
    return [str(step) for step in steps]


def verify_result(user_request: str, tool_output: str, tool_error: str) -> str:
    """
    Phase 11 'Verify' node. Returns one of:
      "complete"     - output satisfies the request
      "error"        - tool failed / output is wrong, worth retrying
      "insufficient" - ran fine but doesn't actually answer the request
    """
    system_prompt = (
        "You verify whether a tool's output satisfies the user's original "
        'request. Respond with ONLY a JSON object: {"status": "complete" | '
        '"error" | "insufficient", "reason": "one short sentence"}. '
        "No prose, no markdown."
    )
    user_prompt = (
        f"Original request: {user_request}\n\n"
        f"Tool stdout:\n{tool_output or '(none)'}\n\n"
        f"Tool stderr:\n{tool_error or '(none)'}"
    )
    content = _chat(system_prompt, user_prompt)
    data = _extract_json(content)
    status = data.get("status", "")
    if status not in {"complete", "error", "insufficient"}:
        status = "insufficient"
    return status
