from typing import Any, AsyncIterator
import logging
from backend.router.providers.base import BaseProvider, ProviderChatResponse, ProviderStreamChunk

logger = logging.getLogger(__name__)

class ModelProvider:
    """
    Standard interface for the models subsystem to interact with inference engines.
    Delegates to the existing `backend.router.providers` architecture.
    """
    def __init__(self, backend_provider: BaseProvider):
        self.backend_provider = backend_provider

    async def generate(self, model_id: str, messages: list[dict[str, Any]], **kwargs) -> str:
        """Simple non-streaming text generation."""
        logger.info(f"ModelProvider generating with {model_id}")
        response = await self.backend_provider.chat(model_id, messages, **kwargs)
        return response.content

    async def generate_stream(self, model_id: str, messages: list[dict[str, Any]], **kwargs) -> AsyncIterator[str]:
        """Streaming text generation."""
        async for chunk in self.backend_provider.chat_stream(model_id, messages, **kwargs):
            yield chunk.content

    async def load_model(self, model_id: str) -> bool:
        """Pre-load a model into the backend."""
        return await self.backend_provider.load_model(model_id)

    async def unload_model(self, model_id: str) -> bool:
        """Unload a model from the backend."""
        return await self.backend_provider.unload_model(model_id)

# Singleton global instance (in a real app, use dependency injection)
_global_provider = None

def get_provider() -> ModelProvider:
    global _global_provider
    if not _global_provider:
        # For SIH Demo, we use the Ollama provider by default
        from backend.router.providers.ollama_provider import OllamaProvider
        from backend.settings import get_settings
        settings = get_settings()
        _global_provider = ModelProvider(OllamaProvider(settings.OLLAMA_BASE_URL))
    return _global_provider
