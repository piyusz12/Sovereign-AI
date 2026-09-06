import asyncio
import logging
import uuid
from typing import AsyncIterator, Dict

from backend.model_gateway.schemas import (
    GatewayInferenceRequest,
    GatewayInferenceResponse,
    GatewayStreamChunk,
    GatewayEmbeddingRequest,
    GatewayEmbeddingResponse,
    GatewayRerankRequest,
    GatewayRerankResponse,
    InferenceMetadata,
)
from backend.model_gateway.provider import LLMProvider
from backend.model_gateway.client import OllamaGatewayProvider, VLLMGatewayProvider, InfinityGatewayProvider
from backend.models.registry import get_model
from backend.audit.service import audit_service
from backend.optimization.scheduler import gpu_scheduler
from backend.rag.cache import embedding_cache

logger = logging.getLogger("sovereign.model_gateway")

class ModelGateway:
    def __init__(self):
        self._providers: Dict[str, LLMProvider] = {}
        
    def _get_provider(self, model_id: str) -> LLMProvider:
        backend_type = "ollama"
        model_info = get_model(model_id)
        if model_info:
            backend_type = model_info.backend
            
        if backend_type not in self._providers:
            if backend_type == "vllm":
                self._providers[backend_type] = VLLMGatewayProvider()
            elif backend_type == "infinity":
                self._providers[backend_type] = InfinityGatewayProvider()
            else:
                self._providers[backend_type] = OllamaGatewayProvider()
                
        return self._providers[backend_type]

    async def generate(self, request: GatewayInferenceRequest) -> GatewayInferenceResponse:
        provider = self._get_provider(request.model)
        
        async def _run():
            from backend.optimization.model_manager import opt_model_manager

            if not await opt_model_manager.ensure_loaded(request.model):
                raise RuntimeError(f"Unable to reserve VRAM for model {request.model}")
            try:
                # Basic timeout handling via asyncio.wait_for
                return await asyncio.wait_for(provider.generate(request), timeout=request.timeout)
            except asyncio.TimeoutError:
                logger.error(f"Inference request for {request.model} timed out after {request.timeout}s")
                raise
                
        # Use our GPU scheduler to manage concurrency
        response: GatewayInferenceResponse = await gpu_scheduler.schedule(f"inference-{request.model}", priority=1, coro=_run())
        
        # Log to audit service
        audit_service.log(
            action="model_gateway.generate",
            status="success",
            user_id="system",
            resource_id=request.model,
            resource_type="model",
            metadata=response.metadata.model_dump()
        )
        
        return response

    async def stream(self, request: GatewayInferenceRequest) -> AsyncIterator[GatewayStreamChunk]:
        provider = self._get_provider(request.model)

        # A stream holds KV cache until its terminal chunk, so it must keep the
        # same exclusive GPU lease as non-streaming generation.
        async with gpu_scheduler.exclusive():
            from backend.optimization.model_manager import opt_model_manager

            if not await opt_model_manager.ensure_loaded(request.model):
                raise RuntimeError(f"Unable to reserve VRAM for model {request.model}")
            async for chunk in provider.stream(request):
                if chunk.metadata:
                    audit_service.log(
                        action="model_gateway.stream",
                        status="success",
                        user_id="system",
                        resource_id=request.model,
                        resource_type="model",
                        metadata=chunk.metadata.model_dump(),
                    )
                yield chunk

    async def embed(self, request: GatewayEmbeddingRequest) -> GatewayEmbeddingResponse:
        # Query embeddings are small but frequent. Cache them before touching a
        # serving backend so background indexing cannot steal GPU time from an
        # interactive request.
        cached: list[list[float] | None] = [
            embedding_cache.get(request.model, text, None) for text in request.input
        ]
        missing_indexes = [index for index, embedding in enumerate(cached) if embedding is None]
        if not missing_indexes:
            return GatewayEmbeddingResponse(
                embeddings=[embedding for embedding in cached if embedding is not None],
                metadata=InferenceMetadata(
                    request_id=f"CACHE-{uuid.uuid4().hex[:8].upper()}",
                    model=request.model,
                    provider="local-cache",
                    latency_ms=0.0,
                    output_tokens=0,
                    prompt_tokens=0,
                    status="success",
                ),
            )

        provider = self._get_provider(request.model)
        missing_input = [request.input[index] for index in missing_indexes]
        provider_request = request.model_copy(update={"input": missing_input})
        
        async def _run():
            from backend.optimization.model_manager import opt_model_manager

            if not await opt_model_manager.ensure_loaded(request.model):
                raise RuntimeError(f"Unable to reserve VRAM for model {request.model}")
            return await asyncio.wait_for(provider.embed(provider_request), timeout=request.timeout)
            
        # We also schedule embeddings on the GPU queue so it doesn't OOM alongside heavy models
        response: GatewayEmbeddingResponse = await gpu_scheduler.schedule(f"embed-{request.model}", priority=2, coro=_run())
        for index, embedding in zip(missing_indexes, response.embeddings):
            cached[index] = embedding
            embedding_cache.set(request.model, request.input[index], embedding, None)
        response = GatewayEmbeddingResponse(
            embeddings=[embedding for embedding in cached if embedding is not None],
            metadata=response.metadata,
        )
        
        audit_service.log(
            action="model_gateway.embed",
            status="success",
            user_id="system",
            resource_id=request.model,
            resource_type="model",
            metadata=response.metadata.model_dump()
        )
        return response

    async def rerank(self, request: GatewayRerankRequest) -> GatewayRerankResponse:
        provider = self._get_provider(request.model)
        
        async def _run():
            from backend.optimization.model_manager import opt_model_manager

            if not await opt_model_manager.ensure_loaded(request.model):
                raise RuntimeError(f"Unable to reserve VRAM for model {request.model}")
            return await asyncio.wait_for(provider.rerank(request), timeout=request.timeout)
            
        response: GatewayRerankResponse = await gpu_scheduler.schedule(f"rerank-{request.model}", priority=2, coro=_run())
        
        audit_service.log(
            action="model_gateway.rerank",
            status="success",
            user_id="system",
            resource_id=request.model,
            resource_type="model",
            metadata=response.metadata.model_dump()
        )
        return response

    async def load_model(self, model_id: str) -> bool:
        provider = self._get_provider(model_id)
        return await provider.load_model(model_id)
        
    async def unload_model(self, model_id: str) -> bool:
        provider = self._get_provider(model_id)
        return await provider.unload_model(model_id)

model_gateway = ModelGateway()
