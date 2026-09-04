"""
Sovereign AI Workbench — vLLM Provider (Stub)

Placeholder for vLLM inference backend. Will be implemented in Phase 25+.
vLLM requires WSL2/Linux and will primarily serve the coding model.

Architecture:
    Coder-7B → vLLM (WSL2) → OpenAI-compatible API → Provider → Router
"""

from __future__ import annotations

import logging
from typing import Any, AsyncIterator

from backend.router.providers.base import (
    BaseProvider,
    InferenceMetrics,
    ProviderChatResponse,
    ProviderModelInfo,
    ProviderRunningModel,
    ProviderStreamChunk,
)

logger = logging.getLogger("sovereign.providers.vllm")


class VLLMProvider(BaseProvider):
    """
    vLLM inference provider — stub for Phase 25+.

    vLLM provides high-throughput serving with PagedAttention.
    Will run inside WSL2 since vLLM does not support Windows natively.
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        super().__init__(base_url, provider_name="vllm")

    async def is_running(self) -> bool:
        # TODO Phase 25: Implement via GET /health
        logger.debug("vLLM provider not yet implemented")
        return False

    async def list_models(self) -> list[ProviderModelInfo]:
        return []

    async def model_exists(self, model_id: str) -> bool:
        return False

    async def load_model(self, model_id: str, keep_alive: str = "10m") -> bool:
        logger.warning("vLLM load_model not yet implemented")
        return False

    async def unload_model(self, model_id: str) -> bool:
        return False

    async def running_models(self) -> list[ProviderRunningModel]:
        return []

    async def chat(
        self,
        model_id: str,
        messages: list[dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        keep_alive: str = "10m",
    ) -> ProviderChatResponse:
        return ProviderChatResponse(
            content="[vLLM provider not yet implemented — Phase 25+]",
            model=model_id,
        )

    async def chat_stream(
        self,
        model_id: str,
        messages: list[dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        keep_alive: str = "10m",
    ) -> AsyncIterator[ProviderStreamChunk]:
        yield ProviderStreamChunk(
            content="[vLLM provider not yet implemented — Phase 25+]",
            done=True,
            model=model_id,
        )
