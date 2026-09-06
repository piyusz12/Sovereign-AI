from backend.router.providers.base import BaseProvider
from backend.router.providers.local import OllamaProvider, OpenAICompatibleProvider


def get_provider(provider_name: str, base_url: str | None = None) -> BaseProvider:
    """Return a functional adapter for the configured local provider."""
    normalized = provider_name.lower()
    if normalized == "ollama":
        return OllamaProvider(base_url or "http://localhost:11434")
    if normalized in {"vllm", "litellm"}:
        return OpenAICompatibleProvider(base_url or "http://localhost:8000")
    raise ValueError(f"Unsupported local model provider: {provider_name}")
