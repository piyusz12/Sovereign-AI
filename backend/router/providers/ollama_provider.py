"""
Sovereign AI Workbench — Ollama Provider

Implements BaseProvider for the Ollama inference backend.
Wraps OllamaClient and translates responses into the standardized
provider format used by the router.

This is the primary inference backend for Phases 4–8.
"""

from __future__ import annotations

import logging
from typing import Any, AsyncIterator, Optional

from backend.router.ollama_client import OllamaClient, ollama_client
from backend.router.providers.base import (
    BaseProvider,
    InferenceMetrics,
    ProviderChatResponse,
    ProviderModelInfo,
    ProviderRunningModel,
    ProviderStreamChunk,
)

logger = logging.getLogger("sovereign.providers.ollama")


class OllamaProvider(BaseProvider):
    """
    Ollama inference provider.

    Delegates to OllamaClient for all HTTP communication.
    Translates Ollama-specific response formats into standardized
    ProviderChatResponse / ProviderStreamChunk objects.
    """

    def __init__(self, base_url: str = "http://localhost:11434", client: Optional[OllamaClient] = None):
        super().__init__(base_url, provider_name="ollama")
        self._client = client or OllamaClient(base_url)

    # ── Health ────────────────────────────────────────────────────────────

    async def is_running(self) -> bool:
        return await self._client.is_running()

    # ── Model Management ──────────────────────────────────────────────────

    async def list_models(self) -> list[ProviderModelInfo]:
        models = await self._client.list_models()
        return [
            ProviderModelInfo(
                name=m.name,
                size_bytes=m.size,
                parameter_size=m.parameter_size,
                quantization=m.quantization_level,
                family=m.family,
            )
            for m in models
        ]

    async def model_exists(self, model_id: str) -> bool:
        return await self._client.model_exists(model_id)

    async def load_model(self, model_id: str, keep_alive: str = "10m") -> bool:
        return await self._client.load_model(model_id, keep_alive=keep_alive)

    async def unload_model(self, model_id: str) -> bool:
        return await self._client.unload_model(model_id)

    async def running_models(self) -> list[ProviderRunningModel]:
        running = await self._client.ps()
        return [
            ProviderRunningModel(
                name=m.name,
                vram_used_mb=m.vram_used_mb,
                ram_used_mb=round(m.size_ram / (1024 ** 2)) if m.size_ram else 0,
                expires_at=m.expires_at,
            )
            for m in running
        ]

    # ── Inference ─────────────────────────────────────────────────────────

    async def chat(
        self,
        model_id: str,
        messages: list[dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        keep_alive: str = "10m",
    ) -> ProviderChatResponse:
        resp = await self._client.chat(
            model=model_id,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            keep_alive=keep_alive,
        )
        return ProviderChatResponse(
            content=resp.content,
            model=resp.model,
            metrics=InferenceMetrics(
                tokens_per_sec=resp.tokens_per_sec,
                first_token_ms=resp.first_token_ms,
                total_duration_ms=resp.total_duration_ms,
                eval_count=resp.eval_count,
                prompt_eval_count=resp.prompt_eval_count,
            ),
            done=resp.done,
            finish_reason=resp.done_reason or "stop",
        )

    async def chat_stream(
        self,
        model_id: str,
        messages: list[dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        keep_alive: str = "10m",
    ) -> AsyncIterator[ProviderStreamChunk]:
        async for chunk in self._client.chat_stream(
            model=model_id,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            keep_alive=keep_alive,
        ):
            metrics = None
            if chunk.done:
                tps = 0.0
                if chunk.eval_duration_ns > 0:
                    tps = round(chunk.eval_count / (chunk.eval_duration_ns / 1e9), 2)
                metrics = InferenceMetrics(
                    tokens_per_sec=tps,
                    first_token_ms=round(chunk.prompt_eval_duration_ns / 1e6, 2) if chunk.prompt_eval_duration_ns else 0.0,
                    total_duration_ms=round(chunk.total_duration_ns / 1e6, 2) if chunk.total_duration_ns else 0.0,
                    eval_count=chunk.eval_count,
                )

            yield ProviderStreamChunk(
                content=chunk.content,
                done=chunk.done,
                model=chunk.model,
                metrics=metrics,
            )


# ── Factory ───────────────────────────────────────────────────────────────────

# Default instance using settings
_default_provider: Optional[OllamaProvider] = None


def get_ollama_provider(base_url: str = "http://localhost:11434") -> OllamaProvider:
    """Get or create the default Ollama provider."""
    global _default_provider
    if _default_provider is None:
        _default_provider = OllamaProvider(base_url)
    return _default_provider
