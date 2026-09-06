"""
Sovereign AI Workbench — vLLM Provider (Phase 25)

vLLM inference provider for high-throughput serving with PagedAttention.
Connects to vLLM's OpenAI-compatible API endpoint.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, AsyncIterator

import httpx

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
    vLLM inference provider (Phase 25).

    Connects to vLLM running usually inside WSL2 or a dedicated Linux environment
    since vLLM does not natively support Windows.
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        super().__init__(base_url, provider_name="vllm")
        self.api_base = f"{self.base_url.rstrip('/')}/v1"

    async def is_running(self) -> bool:
        """Check if vLLM server is accessible."""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.get(f"{self.base_url}/health")
                return resp.status_code == 200
        except Exception as e:
            logger.debug(f"vLLM health check failed: {e}")
            return False

    async def list_models(self) -> list[ProviderModelInfo]:
        """Fetch available models from vLLM."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.api_base}/models")
                if resp.status_code == 200:
                    data = resp.json()
                    models = []
                    for model in data.get("data", []):
                        models.append(
                            ProviderModelInfo(
                                name=model.get("id", "unknown"),
                                size_bytes=0,
                                parameter_size="unknown",
                            )
                        )
                    return models
        except Exception as e:
            logger.debug(f"Failed to list vLLM models: {e}")
        return []

    async def model_exists(self, model_id: str) -> bool:
        """Check if a specific model exists on vLLM."""
        models = await self.list_models()
        return any(m.name == model_id for m in models)

    async def load_model(self, model_id: str, keep_alive: str = "10m") -> bool:
        """vLLM models are generally loaded at startup; dynamic loading isn't standard natively."""
        logger.debug(f"vLLM dummy load_model called for {model_id}")
        return True

    async def unload_model(self, model_id: str) -> bool:
        """vLLM doesn't support dynamic unloading natively via standard API."""
        logger.debug(f"vLLM dummy unload_model called for {model_id}")
        return True

    async def running_models(self) -> list[ProviderRunningModel]:
        """vLLM has one active model typically, list_models effectively returns the running model."""
        models = await self.list_models()
        return [
            ProviderRunningModel(
                name=m.name,
                size_bytes=m.size_bytes,
                expires_at="never",
            )
            for m in models
        ]

    async def chat(
        self,
        model_id: str,
        messages: list[dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        keep_alive: str = "10m",
    ) -> ProviderChatResponse:
        start_time = time.time()
        
        payload = {
            "model": model_id,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                logger.debug(f"Sending vLLM chat request to {self.api_base}/chat/completions")
                resp = await client.post(
                    f"{self.api_base}/chat/completions",
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                logger.error(f"vLLM chat request failed: {e}")
                raise

        duration_ms = round((time.time() - start_time) * 1000, 2)
        content = data["choices"][0]["message"].get("content", "")
        
        usage = data.get("usage", {})
        prompt_eval_count = usage.get("prompt_tokens", 0)
        eval_count = usage.get("completion_tokens", 0)
        
        tps = 0.0
        if eval_count > 0 and duration_ms > 0:
            tps = round(eval_count / (duration_ms / 1000.0), 2)

        return ProviderChatResponse(
            content=content,
            model=model_id,
            metrics=InferenceMetrics(
                tokens_per_sec=tps,
                first_token_ms=0.0,
                total_duration_ms=duration_ms,
                eval_count=eval_count,
                prompt_eval_count=prompt_eval_count,
            )
        )

    async def chat_stream(
        self,
        model_id: str,
        messages: list[dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        keep_alive: str = "10m",
    ) -> AsyncIterator[ProviderStreamChunk]:
        start_time = time.time()
        first_token_time = 0.0
        
        payload = {
            "model": model_id,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
            "stream_options": {"include_usage": True},
        }

        eval_count = 0
        prompt_eval_count = 0

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST", 
                f"{self.api_base}/chat/completions", 
                json=payload,
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    
                    data_str = line[len("data: "):]
                    if data_str.strip() == "[DONE]":
                        break
                        
                    try:
                        chunk = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue
                        
                    choices = chunk.get("choices", [])
                    if choices:
                        delta = choices[0].get("delta", {})
                        if "content" in delta:
                            if first_token_time == 0.0:
                                first_token_time = time.time()
                            eval_count += 1
                            yield ProviderStreamChunk(content=delta["content"], done=False, model=model_id)
                    
                    if "usage" in chunk and chunk["usage"]:
                        usage = chunk["usage"]
                        eval_count = usage.get("completion_tokens", eval_count)
                        prompt_eval_count = usage.get("prompt_tokens", prompt_eval_count)

        duration_ms = round((time.time() - start_time) * 1000, 2)
        first_token_ms = round((first_token_time - start_time) * 1000, 2) if first_token_time > 0 else 0.0
        tps = 0.0
        if eval_count > 0 and duration_ms > 0:
            tps = round(eval_count / (duration_ms / 1000.0), 2)
            
        yield ProviderStreamChunk(
            content="",
            done=True,
            model=model_id,
            metrics=InferenceMetrics(
                tokens_per_sec=tps,
                first_token_ms=first_token_ms,
                total_duration_ms=duration_ms,
                eval_count=eval_count,
                prompt_eval_count=prompt_eval_count,
            )
        )
