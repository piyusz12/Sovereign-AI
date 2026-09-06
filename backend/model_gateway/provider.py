from __future__ import annotations

import abc
from typing import AsyncIterator

from backend.model_gateway.schemas import GatewayInferenceRequest, GatewayInferenceResponse, GatewayStreamChunk

class LLMProvider(abc.ABC):
    """
    Abstract Base Class for local inference providers.
    """
    
    @abc.abstractmethod
    async def generate(self, request: GatewayInferenceRequest) -> GatewayInferenceResponse:
        ...

    @abc.abstractmethod
    async def stream(self, request: GatewayInferenceRequest) -> AsyncIterator[GatewayStreamChunk]:
        ...
        if False:
            yield  # pragma: no cover

    @abc.abstractmethod
    async def load_model(self, model_id: str) -> bool:
        ...

    @abc.abstractmethod
    async def unload_model(self, model_id: str) -> bool:
        ...

    @abc.abstractmethod
    async def is_running(self) -> bool:
        ...
