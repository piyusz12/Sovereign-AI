from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Optional
from pydantic import BaseModel

class ProviderMetrics(BaseModel):
    tokens_per_sec: float = 0.0
    first_token_ms: float = 0.0
    total_duration_ms: float = 0.0
    eval_count: int = 0
    prompt_eval_count: int = 0

class ProviderChatResponse(BaseModel):
    content: str
    metrics: ProviderMetrics = ProviderMetrics()

class ProviderStreamChunk(BaseModel):
    content: str = ""
    done: bool = False
    metrics: Optional[ProviderMetrics] = None

class BaseProvider(ABC):
    @abstractmethod
    async def chat(self, *args, **kwargs) -> ProviderChatResponse:
        pass
        
    @abstractmethod
    async def chat_stream(self, *args, **kwargs) -> AsyncIterator[ProviderStreamChunk]:
        yield ProviderStreamChunk(done=True)

    @abstractmethod
    async def model_exists(self, model_id: str) -> bool:
        """Return whether a locally configured model can be served."""
        pass

    @abstractmethod
    async def load_model(self, model_id: str, keep_alive: str = "5m") -> bool:
        """Warm a model before the next inference request."""
        pass

    @abstractmethod
    async def unload_model(self, model_id: str) -> bool:
        """Evict a model so another heavy model can use the GPU."""
        pass

    @abstractmethod
    async def running_models(self) -> list[Any]:
        """Return provider-native running-model objects with VRAM metadata."""
        pass
