"""
Sovereign AI Workbench — vLLM Client

Async HTTP client for vLLM REST API (OpenAI-compatible endpoints).
vLLM typically runs in WSL2 on port 8000.
"""

import httpx
import logging
import json
from typing import Any, AsyncIterator, Optional, List, Dict
from dataclasses import dataclass

from backend.settings import settings

logger = logging.getLogger("sovereign.vllm_client")

INFERENCE_TIMEOUT = 120.0
METADATA_TIMEOUT = 5.0

@dataclass
class VllmModel:
    id: str
    object: str
    created: int
    owned_by: str

@dataclass
class VllmChatChunk:
    content: str
    done: bool

class VllmClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or settings.vllm_base_url).rstrip("/")
        # vLLM exposes OpenAI endpoints under /v1
        self.api_url = f"{self.base_url}/v1"

    def _client(self, timeout: float) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self.api_url,
            timeout=httpx.Timeout(timeout, connect=5.0)
        )

    async def is_running(self) -> bool:
        """Check if vLLM is reachable by listing models."""
        async with self._client(METADATA_TIMEOUT) as client:
            try:
                resp = await client.get("/models")
                return resp.status_code == 200
            except Exception:
                return False

    async def list_models(self) -> List[VllmModel]:
        async with self._client(METADATA_TIMEOUT) as client:
            try:
                resp = await client.get("/models")
                resp.raise_for_status()
                data = resp.json()
                return [
                    VllmModel(
                        id=m["id"],
                        object=m.get("object", "model"),
                        created=m.get("created", 0),
                        owned_by=m.get("owned_by", "vllm")
                    )
                    for m in data.get("data", [])
                ]
            except Exception as e:
                logger.error(f"Failed to list vLLM models: {e}")
                return []

    async def chat(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """Non-streaming OpenAI-compatible chat completion."""
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        async with self._client(INFERENCE_TIMEOUT) as client:
            resp = await client.post("/chat/completions", json=payload)
            resp.raise_for_status()
            return resp.json()

    async def chat_stream(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> AsyncIterator[VllmChatChunk]:
        """Streaming OpenAI-compatible chat completion."""
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True
        }
        async with self._client(INFERENCE_TIMEOUT) as client:
            async with client.stream("POST", "/chat/completions", json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith("data: "):
                        line = line[6:]
                    if line == "[DONE]":
                        yield VllmChatChunk(content="", done=True)
                        break
                        
                    try:
                        data = json.loads(line)
                        choices = data.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {})
                            content = delta.get("content", "")
                            # If finish_reason is set, we are done
                            finish_reason = choices[0].get("finish_reason")
                            
                            yield VllmChatChunk(content=content, done=bool(finish_reason))
                    except json.JSONDecodeError:
                        continue

vllm_client = VllmClient()
