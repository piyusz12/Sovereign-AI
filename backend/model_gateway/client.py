import logging
import time
import uuid
from typing import AsyncIterator, Optional, List

from backend.settings import settings
from backend.model_gateway.schemas import (
    GatewayInferenceRequest,
    GatewayInferenceResponse,
    GatewayStreamChunk,
    GatewayEmbeddingRequest,
    GatewayEmbeddingResponse,
    GatewayRerankRequest,
    GatewayRerankResponse,
    InferenceMetadata
)
import httpx
from backend.model_gateway.provider import LLMProvider
from backend.router.ollama_client import OllamaClient
from backend.router.vllm_client import VllmClient

logger = logging.getLogger("sovereign.model_gateway.client")


def _provider_model_id(model_id: str) -> str:
    """Resolve internal registry IDs to the provider's actual local model tag."""
    from backend.models.registry import get_model

    model = get_model(model_id)
    return model.name if model else model_id

class OllamaGatewayProvider(LLMProvider):
    def __init__(self, base_url: str = settings.ollama_base_url):
        self._client = OllamaClient(base_url)
        self.provider_name = "ollama"

    async def generate(self, request: GatewayInferenceRequest) -> GatewayInferenceResponse:
        start_time = time.time()
        
        # We need to map `ChatMessage` to dict
        messages = [msg.model_dump() for msg in request.messages]
        
        resp = await self._client.chat(
            model=_provider_model_id(request.model),
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            keep_alive="10m",
            response_format=request.response_format,
        )
        
        latency_ms = (time.time() - start_time) * 1000
        
        metadata = InferenceMetadata(
            request_id=f"REQ-{uuid.uuid4().hex[:8].upper()}",
            model=request.model,
            provider=self.provider_name,
            latency_ms=latency_ms,
            output_tokens=resp.eval_count,
            prompt_tokens=resp.prompt_eval_count,
            status="success",
            finish_reason=resp.done_reason or "stop"
        )
        
        return GatewayInferenceResponse(
            content=resp.content,
            metadata=metadata
        )

    async def stream(self, request: GatewayInferenceRequest) -> AsyncIterator[GatewayStreamChunk]:
        messages = [msg.model_dump() for msg in request.messages]
        start_time = time.time()
        request_id = f"REQ-{uuid.uuid4().hex[:8].upper()}"
        
        async for chunk in self._client.chat_stream(
            model=_provider_model_id(request.model),
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            keep_alive="10m",
        ):
            metadata = None
            if chunk.done:
                latency_ms = (time.time() - start_time) * 1000
                metadata = InferenceMetadata(
                    request_id=request_id,
                    model=request.model,
                    provider=self.provider_name,
                    latency_ms=latency_ms,
                    output_tokens=chunk.eval_count,
                    prompt_tokens=0, # Ollama stream doesn't give prompt tokens perfectly sometimes
                    status="success",
                    finish_reason="stop"
                )
                
            yield GatewayStreamChunk(
                content=chunk.content,
                done=chunk.done,
                metadata=metadata
            )

    async def embed(self, request: GatewayEmbeddingRequest) -> GatewayEmbeddingResponse:
        raise NotImplementedError("Ollama embeddings not implemented via Gateway yet.")

    async def rerank(self, request: GatewayRerankRequest) -> GatewayRerankResponse:
        raise NotImplementedError("Ollama reranking not implemented via Gateway yet.")

    async def load_model(self, model_id: str) -> bool:
        return await self._client.load_model(_provider_model_id(model_id))

    async def unload_model(self, model_id: str) -> bool:
        return await self._client.unload_model(_provider_model_id(model_id))

    async def is_running(self) -> bool:
        return await self._client.is_running()


class VLLMGatewayProvider(LLMProvider):
    def __init__(self, base_url: str = settings.vllm_base_url):
        self._client = VllmClient(base_url)
        self.provider_name = "vllm"

    async def generate(self, request: GatewayInferenceRequest) -> GatewayInferenceResponse:
        start_time = time.time()
        messages = [msg.model_dump() for msg in request.messages]
        
        resp = await self._client.chat(
            model=request.model,
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        
        choices = resp.get("choices", [])
        content = ""
        finish_reason = "stop"
        if choices:
            content = choices[0].get("message", {}).get("content", "")
            finish_reason = choices[0].get("finish_reason") or "stop"
            
        usage = resp.get("usage", {})
        latency_ms = (time.time() - start_time) * 1000
        
        metadata = InferenceMetadata(
            request_id=f"REQ-{uuid.uuid4().hex[:8].upper()}",
            model=request.model,
            provider=self.provider_name,
            latency_ms=latency_ms,
            output_tokens=usage.get("completion_tokens", 0),
            prompt_tokens=usage.get("prompt_tokens", 0),
            status="success",
            finish_reason=finish_reason
        )
        
        return GatewayInferenceResponse(
            content=content,
            metadata=metadata
        )

    async def stream(self, request: GatewayInferenceRequest) -> AsyncIterator[GatewayStreamChunk]:
        messages = [msg.model_dump() for msg in request.messages]
        start_time = time.time()
        request_id = f"REQ-{uuid.uuid4().hex[:8].upper()}"
        
        output_tokens = 0
        async for chunk in self._client.chat_stream(
            model=request.model,
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        ):
            output_tokens += 1
            metadata = None
            if chunk.done:
                latency_ms = (time.time() - start_time) * 1000
                metadata = InferenceMetadata(
                    request_id=request_id,
                    model=request.model,
                    provider=self.provider_name,
                    latency_ms=latency_ms,
                    output_tokens=output_tokens,
                    prompt_tokens=0,
                    status="success",
                    finish_reason="stop"
                )
            
            yield GatewayStreamChunk(
                content=chunk.content,
                done=chunk.done,
                metadata=metadata
            )

    async def embed(self, request: GatewayEmbeddingRequest) -> GatewayEmbeddingResponse:
        raise NotImplementedError("vLLM does not support embeddings.")

    async def rerank(self, request: GatewayRerankRequest) -> GatewayRerankResponse:
        raise NotImplementedError("vLLM does not support reranking.")

    async def load_model(self, model_id: str) -> bool:
        logger.info(f"vLLM: Assuming model {model_id} is already loaded.")
        return True

    async def unload_model(self, model_id: str) -> bool:
        logger.warning(f"vLLM: Unload requested for {model_id}, but vLLM does not support dynamic eviction.")
        return True

    async def is_running(self) -> bool:
        return await self._client.is_running()


class InfinityGatewayProvider(LLMProvider):
    def __init__(self, base_url: str = settings.infinity_base_url):
        self.base_url = base_url
        self.provider_name = "infinity"

    async def generate(self, request: GatewayInferenceRequest) -> GatewayInferenceResponse:
        raise NotImplementedError("Infinity does not support text generation.")

    async def stream(self, request: GatewayInferenceRequest) -> AsyncIterator[GatewayStreamChunk]:
        raise NotImplementedError("Infinity does not support text generation.")
        if False:
            yield

    async def embed(self, request: GatewayEmbeddingRequest) -> GatewayEmbeddingResponse:
        start_time = time.time()
        async with httpx.AsyncClient(timeout=request.timeout) as client:
            response = await client.post(
                f"{self.base_url}/v1/embeddings",
                json={"model": request.model, "input": request.input},
            )
            response.raise_for_status()
            data = response.json()
            
            embeddings = []
            if "data" in data and isinstance(data["data"], list):
                embeddings = [item["embedding"] for item in data["data"]]
                
        latency_ms = (time.time() - start_time) * 1000
        
        metadata = InferenceMetadata(
            request_id=f"REQ-{uuid.uuid4().hex[:8].upper()}",
            model=request.model,
            provider=self.provider_name,
            latency_ms=latency_ms,
            output_tokens=data.get("usage", {}).get("total_tokens", 0),
            prompt_tokens=data.get("usage", {}).get("prompt_tokens", 0),
            status="success",
            finish_reason="stop"
        )
        return GatewayEmbeddingResponse(embeddings=embeddings, metadata=metadata)

    async def rerank(self, request: GatewayRerankRequest) -> GatewayRerankResponse:
        start_time = time.time()
        async with httpx.AsyncClient(timeout=request.timeout) as client:
            response = await client.post(
                f"{self.base_url}/rerank",
                json={
                    "model": request.model,
                    "query": request.query,
                    "documents": request.documents
                },
            )
            response.raise_for_status()
            data = response.json()
            
            scores = [0.0] * len(request.documents)
            if "results" in data:
                for result in data["results"]:
                    idx = result.get("index")
                    if idx is not None and 0 <= idx < len(request.documents):
                        scores[idx] = result.get("relevance_score", 0.0)
                        
        latency_ms = (time.time() - start_time) * 1000
        
        metadata = InferenceMetadata(
            request_id=f"REQ-{uuid.uuid4().hex[:8].upper()}",
            model=request.model,
            provider=self.provider_name,
            latency_ms=latency_ms,
            output_tokens=data.get("usage", {}).get("total_tokens", 0),
            prompt_tokens=data.get("usage", {}).get("prompt_tokens", 0),
            status="success",
            finish_reason="stop"
        )
        return GatewayRerankResponse(scores=scores, metadata=metadata)

    async def load_model(self, model_id: str) -> bool:
        logger.info(f"Infinity: Assuming model {model_id} is loaded.")
        return True

    async def unload_model(self, model_id: str) -> bool:
        logger.info(f"Infinity: Unload requested for {model_id}, no-op.")
        return True

    async def is_running(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception:
            return False
