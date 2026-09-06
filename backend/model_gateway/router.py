import asyncio
import logging
from typing import AsyncIterator, Dict

from backend.model_gateway.schemas import (
    GatewayInferenceRequest,
    GatewayInferenceResponse,
    GatewayStreamChunk
)
from backend.model_gateway.provider import LLMProvider
from backend.model_gateway.client import OllamaGatewayProvider, VLLMGatewayProvider
from backend.models.registry import get_model
from backend.audit.service import audit_service
from backend.optimization.scheduler import gpu_scheduler

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
            else:
                self._providers[backend_type] = OllamaGatewayProvider()
                
        return self._providers[backend_type]

    async def generate(self, request: GatewayInferenceRequest) -> GatewayInferenceResponse:
        provider = self._get_provider(request.model)
        
        async def _run():
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
        
        # We manually acquire the lock for streams
        job_id = f"stream-{request.model}"
        gpu_scheduler.queue_depth += 1
        
        try:
            async with gpu_scheduler.semaphore:
                # We can't wrap the entire async for in wait_for easily without custom timeout tracking
                # per chunk. A simplified stream execution:
                async for chunk in provider.stream(request):
                    if chunk.metadata:
                        # Log the final completion
                        audit_service.log(
                            action="model_gateway.stream",
                            status="success",
                            user_id="system",
                            resource_id=request.model,
                            resource_type="model",
                            metadata=chunk.metadata.model_dump()
                        )
                    yield chunk
        finally:
            gpu_scheduler.queue_depth -= 1

    async def load_model(self, model_id: str) -> bool:
        provider = self._get_provider(model_id)
        return await provider.load_model(model_id)
        
    async def unload_model(self, model_id: str) -> bool:
        provider = self._get_provider(model_id)
        return await provider.unload_model(model_id)

model_gateway = ModelGateway()
