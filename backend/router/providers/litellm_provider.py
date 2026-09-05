import json
import logging
import time
from typing import Any, AsyncIterator, Optional

import httpx

from backend.router.providers.base import BaseProvider, ProviderChatResponse, ProviderStreamChunk, InferenceMetrics
from backend.router.providers.ollama_provider import OllamaProvider

logger = logging.getLogger("sovereign.providers.litellm")


class LiteLLMProvider(BaseProvider):
    """
    LiteLLM Provider using the OpenAI-compatible REST API.
    
    This provider forwards inference requests to a local LiteLLM proxy server 
    (which acts as the Dynamic Expertise Broker).
    
    Because LiteLLM itself does not expose Ollama's hardware lifecycle APIs 
    (load/unload/VRAM checking), this provider delegates those methods to 
    a hidden OllamaProvider to maintain the strict single-GPU discipline.
    """

    def __init__(self, base_url: str = "http://localhost:4000"):
        super().__init__(base_url, "litellm")
        self.api_base = f"{base_url.rstrip('/')}/v1"
        self._ollama = OllamaProvider("http://localhost:11434")

    async def is_running(self) -> bool:
        """Check if the LiteLLM proxy is reachable."""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                # LiteLLM proxy health endpoint
                resp = await client.get(f"{self.base_url}/health")
                return resp.status_code == 200
        except Exception:
            return False

    async def chat(
        self,
        model_id: str,
        messages: list[dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        keep_alive: str = "5m",
    ) -> ProviderChatResponse:
        start_time = time.time()
        
        # OpenAI schema format
        payload = {
            "model": model_id,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        headers = {
            "Authorization": "Bearer sk-local-sovereign-key",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                logger.debug(f"Sending LiteLLM chat request to {self.api_base}/chat/completions for model {model_id}")
                resp = await client.post(
                    f"{self.api_base}/chat/completions",
                    json=payload,
                    headers=headers,
                )
                resp.raise_for_status()
                data = resp.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"LiteLLM HTTP error: {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"LiteLLM Request error: {e}")
                raise

        duration_ms = round((time.time() - start_time) * 1000, 2)
        content = data["choices"][0]["message"].get("content", "")
        
        # OpenAI doesn't natively expose eval_count / first_token_ms in the same way 
        # as Ollama, but LiteLLM includes 'usage'
        usage = data.get("usage", {})
        prompt_eval_count = usage.get("prompt_tokens", 0)
        eval_count = usage.get("completion_tokens", 0)
        
        tps = 0.0
        if eval_count > 0 and duration_ms > 0:
            tps = round(eval_count / (duration_ms / 1000.0), 2)

        return ProviderChatResponse(
            content=content,
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
        keep_alive: str = "5m",
    ) -> AsyncIterator[ProviderStreamChunk]:
        start_time = time.time()
        first_token_time = 0.0
        
        payload = {
            "model": model_id,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
            "stream_options": {"include_usage": True} # OpenAI standard to get usage in stream
        }

        eval_count = 0
        prompt_eval_count = 0

        headers = {
            "Authorization": "Bearer sk-local-sovereign-key",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST", 
                f"{self.api_base}/chat/completions", 
                json=payload,
                headers=headers
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
                            yield ProviderStreamChunk(content=delta["content"], done=False)
                    
                    # Last chunk with stream_options usually contains usage
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
            metrics=InferenceMetrics(
                tokens_per_sec=tps,
                first_token_ms=first_token_ms,
                total_duration_ms=duration_ms,
                eval_count=eval_count,
                prompt_eval_count=prompt_eval_count,
            )
        )

    # ── Delegate Hardware Lifecycle to Ollama ─────────────────────────────
    
    async def list_models(self) -> list[Any]:
        # Return mocked models based on aliases since LiteLLM doesn't easily expose this to the provider abstraction
        from backend.router.providers.base import ProviderModelInfo
        return [
            ProviderModelInfo(name="sovereign-reasoning", size_bytes=8*1024**3, parameter_size="14b"),
            ProviderModelInfo(name="sovereign-coding", size_bytes=4*1024**3, parameter_size="7b"),
            ProviderModelInfo(name="sovereign-vision", size_bytes=5*1024**3, parameter_size="8b"),
        ]

    async def model_exists(self, model_id: str) -> bool:
        return True

    async def load_model(self, model_id: str, keep_alive: str = "5m") -> bool:
        # Mapping LiteLLM aliases to Ollama models
        ollama_mapping = {
            "sovereign-reasoning": "qwen3:14b",
            "sovereign-coding": "qwen2.5-coder:7b",
            "sovereign-vision": "qwen3-vl:8b"
        }
        actual_model = ollama_mapping.get(model_id, model_id)
        logger.debug(f"LiteLLMProvider delegating load_model for {model_id} (Ollama: {actual_model})")
        return await self._ollama.load_model(actual_model, keep_alive)

    async def unload_model(self, model_id: str) -> bool:
        ollama_mapping = {
            "sovereign-reasoning": "qwen3:14b",
            "sovereign-coding": "qwen2.5-coder:7b",
            "sovereign-vision": "qwen3-vl:8b"
        }
        actual_model = ollama_mapping.get(model_id, model_id)
        logger.debug(f"LiteLLMProvider delegating unload_model for {model_id} (Ollama: {actual_model})")
        return await self._ollama.unload_model(actual_model)

    async def running_models(self) -> list[Any]:
        # Return the underlying Ollama models
        return await self._ollama.running_models()
