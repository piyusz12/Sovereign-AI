from abc import ABC, abstractmethod
from typing import AsyncIterator, List, Dict, Any, Optional
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
