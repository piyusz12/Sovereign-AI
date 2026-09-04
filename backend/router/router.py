"""
Sovereign AI Workbench — Model Router

Routes classified tasks to the appropriate model, handling model loading/unloading
to respect single-GPU discipline on the RTX 4060 8GB.

Architecture:
    User Request → Task Classifier → Model Router → Provider → Response

Phase 5: Uses provider abstraction — router never imports a specific backend.
Phase 6: Hybrid classification (keyword + LLM), routing decisions with full trace.
Phase 7: Coding-specific system prompts and code generation support.
"""

from __future__ import annotations

import logging
import time
from typing import Any, AsyncIterator, Optional

from backend.router.model_registry import ModelRegistry, ModelConfig, model_registry
from backend.router.task_classifier import (
    TaskClassifier,
    ClassificationResult,
    task_classifier,
    TASK_TYPE_TO_CATEGORY,
    TASK_TYPE_TO_MODEL_NAME,
)
from backend.router.routing_policy import (
    ClassificationSignal,
    RoutingDecision,
    RoutingPolicy,
    default_policy,
)
from backend.router.llm_classifier import LLMClassifier, llm_classifier
from backend.router.coding import (
    extract_code_blocks,
    get_system_prompt as get_coding_system_prompt,
    CodeGenerationResult,
)
from backend.router.providers.base import BaseProvider, ProviderChatResponse, ProviderStreamChunk
from backend.router.providers.factory import get_provider
from backend.router.session_manager import session_manager, SessionManager

logger = logging.getLogger("sovereign.router")


# ── Category mapping ──────────────────────────────────────────────────────────

TASK_TO_CATEGORY: dict[str, str] = {
    "reasoning": "reasoning",
    "coding": "coding",
    "vision": "vision",
    "document_reasoning": "reasoning",
    "data_analysis": "coding",
    "general": "reasoning",
}


class ModelRouter:
    """
    Routes requests to the appropriate local model.

    The router:
    1. Classifies the task type (keyword-first, LLM fallback)
    2. Selects the model from the registry
    3. Ensures the model is loaded (unloading others if needed)
    4. Gets the correct provider via the factory
    5. Returns the response with full routing decision trace

    All communication is local (localhost only).
    """

    def __init__(
        self,
        registry: Optional[ModelRegistry] = None,
        classifier: Optional[TaskClassifier] = None,
        llm_clf: Optional[LLMClassifier] = None,
        sessions: Optional[SessionManager] = None,
        policy: Optional[RoutingPolicy] = None,
    ):
        self.registry = registry or model_registry
        self.classifier = classifier or task_classifier
        self.llm_clf = llm_clf or llm_classifier
        self.sessions = sessions or session_manager
        self.policy = policy or default_policy

    def _get_provider(self, model: ModelConfig) -> BaseProvider:
        """Get the appropriate provider for a model."""
        return get_provider(model.provider.value, model.base_url)

    # ── Classify Only (Phase 6) ───────────────────────────────────────────

    async def classify_only(
        self,
        user_input: str,
        has_image: bool = False,
        use_llm: bool = False,
    ) -> RoutingDecision:
        """
        Classify a user input and return the routing decision WITHOUT running
        inference. Useful for the frontend to preview routing before committing.

        Args:
            user_input: The user's message
            has_image: Whether the request includes an image
            use_llm: Force LLM classification even for high-confidence keyword matches

        Returns:
            RoutingDecision with full classification trace
        """
        start = time.time()

        # Step 1: Keyword classification
        keyword_signal = self.classifier.classify_with_signal(user_input, has_image)

        # Step 2: Decide if LLM classification is needed
        llm_signal = None
        should_use_llm = (
            use_llm
            or self.policy.prefer_llm
            or keyword_signal.confidence < self.policy.llm_threshold
        )

        if should_use_llm:
            llm_signal = await self._try_llm_classify(user_input)

        # Step 3: Merge signals into final decision
        decision = self._merge_signals(keyword_signal, llm_signal, start)
        return decision

    # ── Route (Phase 5 + 6 upgrade) ───────────────────────────────────────

    async def route(
        self,
        user_input: str,
        has_image: bool = False,
        force_model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        session_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Route a user request to the appropriate model (non-streaming).

        Args:
            user_input: The user's message
            has_image: Whether the request includes an image
            force_model: Force a specific model category (bypasses classifier)
            system_prompt: Optional system prompt override
            temperature: Generation temperature
            max_tokens: Maximum tokens to generate
            session_id: Optional session ID for conversational memory

        Returns:
            Dict with response text, classification info, model metadata, and metrics
        """
        start = time.time()

        # Step 1: Classify (or force)
        if force_model:
            classification = self.classifier.classify(user_input, has_image)
            category = force_model
            routing_decision = RoutingDecision(
                task_type=classification.task_type.value,
                model_category=category,
                model_name=classification.model.value,
                confidence=1.0,
                reason=f"Model forced to '{force_model}'",
            )
        else:
            routing_decision = await self.classify_only(user_input, has_image)
            category = routing_decision.model_category

        logger.info(
            "Task classified as '%s' → model category '%s' (confidence: %.2f)",
            routing_decision.task_type,
            category,
            routing_decision.confidence,
        )

        # Step 2: Load model (triggers VRAM swap if needed)
        model = await self.registry.load_model(category)

        # Step 3: Resolve system prompt
        effective_prompt = self._resolve_system_prompt(
            system_prompt, category, model, routing_decision.task_type
        )

        # Step 4: Send to model via provider
        messages = self._build_messages(user_input, effective_prompt, session_id)
        provider = self._get_provider(model)

        try:
            chat_response = await provider.chat(
                model_id=model.model_id,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                keep_alive=model.keep_alive,
            )
            response_text = chat_response.content
            m = chat_response.metrics
            metrics = {
                "tokens_per_sec": m.tokens_per_sec,
                "first_token_ms": m.first_token_ms,
                "total_duration_ms": m.total_duration_ms,
                "eval_count": m.eval_count,
                "prompt_eval_count": m.prompt_eval_count,
            }
        except ConnectionError as e:
            logger.error("Provider connection failed: %s", e)
            response_text = f"[Error: {e}]"
            metrics = {}
        except Exception as e:
            logger.error("Inference failed: %s", e)
            response_text = f"[Error calling model: {e}]"
            metrics = {}

        duration_ms = round((time.time() - start) * 1000, 2)

        # Save to session history if applicable and successful
        if session_id and response_text and not response_text.startswith("[Error"):
            self.sessions.add_message(session_id, "user", user_input)
            self.sessions.add_message(session_id, "assistant", response_text)

        return {
            "response": response_text,
            "classification": {
                "task_type": routing_decision.task_type,
                "model": routing_decision.model_name,
                "confidence": routing_decision.confidence,
                "reason": routing_decision.reason,
            },
            "routing_decision": routing_decision.to_dict(),
            "model_used": {
                "name": model.name,
                "provider": model.provider.value,
                "model_id": model.model_id,
                "category": category,
            },
            "metrics": metrics,
            "duration_ms": duration_ms,
        }

    # ── Route Streaming ───────────────────────────────────────────────────

    async def route_stream(
        self,
        user_input: str,
        has_image: bool = False,
        force_model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        session_id: Optional[str] = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """
        Route a user request with streaming response.

        Yields dicts suitable for SSE:
            {"chunk": "token text", "done": false}
            ...
            {"chunk": "", "done": true, "classification": {...}, "model_used": {...}, "metrics": {...}}
        """
        start = time.time()

        # Step 1: Classify
        if force_model:
            classification = self.classifier.classify(user_input, has_image)
            category = force_model
            routing_decision = RoutingDecision(
                task_type=classification.task_type.value,
                model_category=category,
                model_name=classification.model.value,
                confidence=1.0,
                reason=f"Model forced to '{force_model}'",
            )
        else:
            routing_decision = await self.classify_only(user_input, has_image)
            category = routing_decision.model_category

        logger.info(
            "Streaming: task '%s' → model '%s'",
            routing_decision.task_type,
            category,
        )

        # Step 2: Load model
        model = await self.registry.load_model(category)

        # Step 3: Resolve system prompt
        effective_prompt = self._resolve_system_prompt(
            system_prompt, category, model, routing_decision.task_type
        )

        # Step 4: Stream from provider
        messages = self._build_messages(user_input, effective_prompt, session_id)
        provider = self._get_provider(model)
        full_response = []

        try:
            async for chunk in provider.chat_stream(
                model_id=model.model_id,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                keep_alive=model.keep_alive,
            ):
                if chunk.done:
                    # Final chunk with metrics
                    duration_ms = round((time.time() - start) * 1000, 2)
                    m = chunk.metrics or ProviderStreamChunk().metrics
                    tps = m.tokens_per_sec if m else 0.0
                    eval_count = m.eval_count if m else 0

                    yield {
                        "chunk": chunk.content,
                        "done": True,
                        "classification": {
                            "task_type": routing_decision.task_type,
                            "model": routing_decision.model_name,
                            "confidence": routing_decision.confidence,
                            "reason": routing_decision.reason,
                        },
                        "routing_decision": routing_decision.to_dict(),
                        "model_used": {
                            "name": model.name,
                            "provider": model.provider.value,
                            "model_id": model.model_id,
                            "category": category,
                        },
                        "metrics": {
                            "tokens_per_sec": tps,
                            "eval_count": eval_count,
                            "duration_ms": duration_ms,
                        },
                    }

                    if session_id and full_response:
                        self.sessions.add_message(session_id, "user", user_input)
                        self.sessions.add_message(session_id, "assistant", "".join(full_response))

                else:
                    full_response.append(chunk.content)
                    yield {
                        "chunk": chunk.content,
                        "done": False,
                    }

        except ConnectionError as e:
            yield {
                "chunk": f"[Error: {e}]",
                "done": True,
                "error": str(e),
            }
        except Exception as e:
            logger.error("Streaming inference failed: %s", e)
            yield {
                "chunk": f"[Error: {e}]",
                "done": True,
                "error": str(e),
            }

    # ── Code Generation (Phase 7) ─────────────────────────────────────────

    async def generate_code(
        self,
        prompt: str,
        language: str = "python",
        context: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> CodeGenerationResult:
        """
        Generate code using the coder model with specialized system prompt.

        Forces the coder model regardless of classification, uses the coding
        system prompt, and extracts structured code blocks from the response.

        Args:
            prompt: Description of the code to generate
            language: Target language (default: "python")
            context: Additional context (file contents, requirements, etc.)
            temperature: Lower temperature for more deterministic code
            max_tokens: Maximum tokens to generate

        Returns:
            CodeGenerationResult with extracted code blocks and metadata
        """
        start = time.time()

        # Build the full prompt
        full_prompt = prompt
        if context:
            full_prompt = f"Context:\n{context}\n\nTask:\n{prompt}"

        if language != "python":
            full_prompt += f"\n\nGenerate code in {language}."

        try:
            result = await self.route(
                user_input=full_prompt,
                force_model="coding",
                system_prompt=get_coding_system_prompt(
                    # Use data_analysis prompt if the prompt looks data-heavy
                    "data_analysis" if any(
                        kw in prompt.lower()
                        for kw in ["data", "csv", "xlsx", "telemetry", "sensor", "analyze"]
                    ) else "coding"
                ),
                temperature=temperature,
                max_tokens=max_tokens,
            )

            response_text = result.get("response", "")
            model_used = result.get("model_used", {}).get("model_id", "")
            duration_ms = round((time.time() - start) * 1000, 2)

            # Extract code blocks
            blocks = extract_code_blocks(response_text)

            return CodeGenerationResult(
                code_blocks=blocks,
                raw_response=response_text,
                model_used=model_used,
                language=language,
                duration_ms=duration_ms,
                success=len(blocks) > 0,
                error=None if blocks else "No code blocks extracted from model response",
            )

        except Exception as e:
            duration_ms = round((time.time() - start) * 1000, 2)
            logger.error("Code generation failed: %s", e)
            return CodeGenerationResult(
                raw_response="",
                model_used="",
                language=language,
                duration_ms=duration_ms,
                success=False,
                error=str(e),
            )

    # ── Internal Helpers ──────────────────────────────────────────────────

    async def _try_llm_classify(
        self,
        user_input: str,
    ) -> Optional[ClassificationSignal]:
        """
        Attempt LLM classification using the active reasoning model.
        Returns None if no reasoning model is available or if the call fails.
        """
        # Get the reasoning model's provider
        reasoning_model = self.registry.get_model("reasoning")
        if not reasoning_model:
            logger.debug("No reasoning model configured — skipping LLM classification")
            return None

        try:
            provider = self._get_provider(reasoning_model)
            return await self.llm_clf.classify(
                user_input=user_input,
                provider=provider,
                model_id=reasoning_model.model_id,
                temperature=self.policy.llm_temperature,
                max_tokens=self.policy.llm_max_tokens,
                timeout_seconds=self.policy.llm_timeout_seconds,
            )
        except Exception as e:
            logger.warning("LLM classification attempt failed: %s", e)
            return None

    def _merge_signals(
        self,
        keyword_signal: ClassificationSignal,
        llm_signal: Optional[ClassificationSignal],
        start_time: float,
    ) -> RoutingDecision:
        """
        Merge keyword and LLM signals into a final routing decision.

        Priority:
        1. If LLM signal exists and has higher confidence → use LLM
        2. Otherwise → use keyword signal
        """
        total_ms = round((time.time() - start_time) * 1000, 2)

        # Determine the winning signal
        if llm_signal and llm_signal.confidence > keyword_signal.confidence:
            winner = llm_signal
            used_llm = True
        else:
            winner = keyword_signal
            used_llm = llm_signal is not None  # LLM was tried but keyword won

        # Map task_type to model category
        category = TASK_TO_CATEGORY.get(winner.task_type, "reasoning")

        return RoutingDecision(
            task_type=winner.task_type,
            model_category=category,
            model_name=winner.model,
            confidence=winner.confidence,
            reason=winner.reason,
            keyword_signal=keyword_signal,
            llm_signal=llm_signal,
            used_llm=used_llm,
            total_classification_ms=total_ms,
            policy_llm_threshold=self.policy.llm_threshold,
            policy_prefer_llm=self.policy.prefer_llm,
        )

    def _resolve_system_prompt(
        self,
        caller_prompt: Optional[str],
        category: str,
        model: ModelConfig,
        task_type: str,
    ) -> str:
        """
        Resolve the system prompt to use, in priority order:
        1. Caller-provided system_prompt
        2. Coding-specific prompt (from coding module) for coding/data_analysis tasks
        3. Model's configured system_prompt
        4. Default reasoning system prompt
        """
        if caller_prompt:
            return caller_prompt

        # Phase 7: Use coding system prompt for coding tasks
        if category == "coding" or task_type in ("coding", "data_analysis"):
            return get_coding_system_prompt(task_type)

        # Use model's configured system prompt
        if model.system_prompt:
            return model.system_prompt

        # Default fallback
        return (
            "You are a Sovereign AI assistant operating entirely on local hardware. "
            "You have access to internal enterprise documents, code execution, and "
            "document generation tools. You must never reference or attempt to access "
            "external services. All your knowledge comes from locally stored documents "
            "and your training data. When you lack internal evidence, say so clearly "
            "rather than fabricating information."
        )

    def _build_messages(
        self,
        user_input: str,
        system_prompt: str,
        session_id: Optional[str] = None,
    ) -> list[dict[str, str]]:
        """Build the messages list for the chat API, including history if present."""
        messages = [{"role": "system", "content": system_prompt}]

        if session_id:
            history = self.sessions.get_history(session_id)
            messages.extend(history)

        messages.append({"role": "user", "content": user_input})
        return messages


# Global instance
model_router = ModelRouter()
