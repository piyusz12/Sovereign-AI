"""
Sovereign AI Workbench — Model Router

Routes classified tasks to the appropriate model, handling model loading/unloading
to respect single-GPU discipline on the RTX 4060 8GB.

Architecture:
    User Request → Task Classifier → Model Router → Selected Model → Response

Phase 4: Now uses OllamaClient for inference and supports streaming.
"""

from __future__ import annotations

import logging
import time
from typing import Any, AsyncIterator, Optional

from backend.router.model_registry import ModelRegistry, ModelConfig, model_registry
from backend.router.task_classifier import TaskClassifier, ClassificationResult, task_classifier
from backend.router.ollama_client import (
    OllamaClient,
    ollama_client,
    ChatResponse,
    StreamChunk,
)

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
    1. Classifies the task type
    2. Selects the model from the registry
    3. Ensures the model is loaded (unloading others if needed)
    4. Sends the request via OllamaClient
    5. Returns the response

    All communication is local (localhost only).
    """

    def __init__(
        self,
        registry: Optional[ModelRegistry] = None,
        classifier: Optional[TaskClassifier] = None,
        client: Optional[OllamaClient] = None,
    ):
        self.registry = registry or model_registry
        self.classifier = classifier or task_classifier
        self._ollama = client or ollama_client

    async def route(
        self,
        user_input: str,
        has_image: bool = False,
        force_model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        """
        Route a user request to the appropriate model (non-streaming).

        Args:
            user_input: The user's message
            has_image: Whether the request includes an image
            force_model: Force a specific model category (bypasses classifier)
            system_prompt: Optional system prompt
            temperature: Generation temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Dict with response text, classification info, model metadata, and metrics
        """
        start = time.time()

        # Step 1: Classify and resolve model category
        classification, category = self._classify(user_input, has_image, force_model)

        logger.info(
            "Task classified as '%s' → model category '%s' (confidence: %.2f)",
            classification.task_type.value,
            category,
            classification.confidence,
        )

        # Step 2: Load model (triggers VRAM swap if needed)
        model = await self.registry.load_model(category)

        # Step 3: Send to model via OllamaClient
        messages = self._build_messages(user_input, system_prompt)

        try:
            chat_response = await self._ollama.chat(
                model=model.model_id,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                keep_alive=model.keep_alive,
            )
            response_text = chat_response.content
            metrics = {
                "tokens_per_sec": chat_response.tokens_per_sec,
                "first_token_ms": chat_response.first_token_ms,
                "total_duration_ms": chat_response.total_duration_ms,
                "eval_count": chat_response.eval_count,
                "prompt_eval_count": chat_response.prompt_eval_count,
            }
        except ConnectionError as e:
            logger.error("Ollama connection failed: %s", e)
            response_text = f"[Error: {e}]"
            metrics = {}
        except Exception as e:
            logger.error("Inference failed: %s", e)
            response_text = f"[Error calling model: {e}]"
            metrics = {}

        duration_ms = round((time.time() - start) * 1000, 2)

        return {
            "response": response_text,
            "classification": {
                "task_type": classification.task_type.value,
                "model": classification.model.value,
                "confidence": classification.confidence,
                "reason": classification.reason,
            },
            "model_used": {
                "name": model.name,
                "provider": model.provider.value,
                "model_id": model.model_id,
                "category": category,
            },
            "metrics": metrics,
            "duration_ms": duration_ms,
        }

    async def route_stream(
        self,
        user_input: str,
        has_image: bool = False,
        force_model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
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
        classification, category = self._classify(user_input, has_image, force_model)

        logger.info(
            "Streaming: task '%s' → model '%s'",
            classification.task_type.value,
            category,
        )

        # Step 2: Load model
        model = await self.registry.load_model(category)

        # Step 3: Stream from OllamaClient
        messages = self._build_messages(user_input, system_prompt)

        try:
            async for chunk in self._ollama.chat_stream(
                model=model.model_id,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                keep_alive=model.keep_alive,
            ):
                if chunk.done:
                    # Final chunk with metrics
                    duration_ms = round((time.time() - start) * 1000, 2)
                    tokens_per_sec = 0.0
                    if chunk.eval_duration_ns > 0:
                        tokens_per_sec = round(
                            chunk.eval_count / (chunk.eval_duration_ns / 1e9), 2
                        )

                    yield {
                        "chunk": chunk.content,
                        "done": True,
                        "classification": {
                            "task_type": classification.task_type.value,
                            "model": classification.model.value,
                            "confidence": classification.confidence,
                            "reason": classification.reason,
                        },
                        "model_used": {
                            "name": model.name,
                            "provider": model.provider.value,
                            "model_id": model.model_id,
                            "category": category,
                        },
                        "metrics": {
                            "tokens_per_sec": tokens_per_sec,
                            "eval_count": chunk.eval_count,
                            "duration_ms": duration_ms,
                        },
                    }
                else:
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

    # ── Internal Helpers ──────────────────────────────────────────────────

    def _classify(
        self,
        user_input: str,
        has_image: bool,
        force_model: Optional[str],
    ) -> tuple[ClassificationResult, str]:
        """
        Classify the task and return (ClassificationResult, model_category).
        If force_model is set, use that category directly.
        """
        classification = self.classifier.classify(user_input, has_image)

        if force_model:
            category = force_model
            classification = ClassificationResult(
                task_type=classification.task_type,
                model=classification.model,
                confidence=1.0,
                reason=f"Model forced to '{force_model}'",
            )
        else:
            category = TASK_TO_CATEGORY.get(
                classification.task_type.value, "reasoning"
            )

        return classification, category

    @staticmethod
    def _build_messages(
        user_input: str,
        system_prompt: Optional[str] = None,
    ) -> list[dict[str, str]]:
        """Build the messages list for the chat API."""
        system = system_prompt or (
            "You are a Sovereign AI assistant operating entirely on local hardware. "
            "You have access to internal enterprise documents, code execution, and "
            "document generation tools. You must never reference or attempt to access "
            "external services. All your knowledge comes from locally stored documents "
            "and your training data. When you lack internal evidence, say so clearly "
            "rather than fabricating information."
        )
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user_input},
        ]


# Global instance
model_router = ModelRouter()
