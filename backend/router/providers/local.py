"""Provider adapters used by the primary router.

They keep the router independent of Ollama/vLLM wire formats while preserving
provider metrics required for TTFT and decode telemetry.
"""

from __future__ import annotations

import time
from typing import Any, AsyncIterator

from backend.router.ollama_client import OllamaClient
from backend.router.providers.base import BaseProvider, ProviderChatResponse, ProviderMetrics, ProviderStreamChunk
from backend.router.vllm_client import VllmClient


class OllamaProvider(BaseProvider):
    def __init__(self, base_url: str) -> None:
        self._client = OllamaClient(base_url)

    async def chat(
        self,
        *,
        model_id: str,
        messages: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
        keep_alive: str,
        response_format: str | dict[str, Any] | None = None,
    ) -> ProviderChatResponse:
        response = await self._client.chat(
            model=model_id,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            keep_alive=keep_alive,
            response_format=response_format,
        )
        return ProviderChatResponse(
            content=response.content,
            metrics=ProviderMetrics(
                tokens_per_sec=response.tokens_per_sec,
                first_token_ms=response.first_token_ms,
                total_duration_ms=response.total_duration_ms,
                eval_count=response.eval_count,
                prompt_eval_count=response.prompt_eval_count,
            ),
        )

    async def chat_stream(self, *, model_id: str, messages: list[dict[str, Any]], temperature: float, max_tokens: int, keep_alive: str) -> AsyncIterator[ProviderStreamChunk]:
        async for chunk in self._client.chat_stream(
            model=model_id,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            keep_alive=keep_alive,
        ):
            metrics = None
            if chunk.done:
                total_ms = round(chunk.total_duration_ns / 1e6, 2) if chunk.total_duration_ns else 0.0
                ttft_ms = round(chunk.prompt_eval_duration_ns / 1e6, 2) if chunk.prompt_eval_duration_ns else 0.0
                tps = 0.0
                if chunk.eval_duration_ns:
                    tps = round(chunk.eval_count / (chunk.eval_duration_ns / 1e9), 2)
                metrics = ProviderMetrics(
                    tokens_per_sec=tps,
                    first_token_ms=ttft_ms,
                    total_duration_ms=total_ms,
                    eval_count=chunk.eval_count,
                )
            yield ProviderStreamChunk(content=chunk.content, done=chunk.done, metrics=metrics)

    async def model_exists(self, model_id: str) -> bool:
        return await self._client.model_exists(model_id)

    async def load_model(self, model_id: str, keep_alive: str = "5m") -> bool:
        return await self._client.load_model(model_id, keep_alive)

    async def unload_model(self, model_id: str) -> bool:
        return await self._client.unload_model(model_id)

    async def running_models(self) -> list[Any]:
        return await self._client.ps()


class OpenAICompatibleProvider(BaseProvider):
    """Adapter for optional vLLM/LiteLLM experiments, not the default path."""

    def __init__(self, base_url: str) -> None:
        self._client = VllmClient(base_url)

    async def chat(
        self,
        *,
        model_id: str,
        messages: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
        keep_alive: str,
        response_format: str | dict[str, Any] | None = None,
    ) -> ProviderChatResponse:
        start = time.perf_counter()
        response = await self._client.chat(model_id, messages, temperature, max_tokens)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        choice = (response.get("choices") or [{}])[0]
        usage = response.get("usage") or {}
        completion_tokens = int(usage.get("completion_tokens") or 0)
        return ProviderChatResponse(
            content=(choice.get("message") or {}).get("content") or "",
            metrics=ProviderMetrics(
                tokens_per_sec=round(completion_tokens / (elapsed_ms / 1000), 2) if elapsed_ms and completion_tokens else 0.0,
                total_duration_ms=elapsed_ms,
                eval_count=completion_tokens,
                prompt_eval_count=int(usage.get("prompt_tokens") or 0),
            ),
        )

    async def chat_stream(self, *, model_id: str, messages: list[dict[str, Any]], temperature: float, max_tokens: int, keep_alive: str) -> AsyncIterator[ProviderStreamChunk]:
        async for chunk in self._client.chat_stream(model_id, messages, temperature, max_tokens):
            yield ProviderStreamChunk(content=chunk.content, done=chunk.done)

    async def model_exists(self, model_id: str) -> bool:
        return any(model.id == model_id for model in await self._client.list_models())

    async def load_model(self, model_id: str, keep_alive: str = "5m") -> bool:
        # vLLM/LiteLLM servers own their model lifecycle; a health check is the
        # only safe portable warm-up operation.
        return await self._client.is_running()

    async def unload_model(self, model_id: str) -> bool:
        return True

    async def running_models(self) -> list[Any]:
        return []
