"""
Sovereign AI Workbench — Base Model Provider

Abstract interface for model inference providers (Ollama, vLLM, Infinity, etc.).
The router uses this interface exclusively — it never imports a specific provider.

Adding a new backend:
    1. Subclass BaseProvider
    2. Implement all abstract methods
    3. Register in provider_factory()
"""

from __future__ import annotations

import abc
import logging
from dataclasses import dataclass
from typing import Any, AsyncIterator, Optional

logger = logging.getLogger("sovereign.providers.base")


# ── Response Types ────────────────────────────────────────────────────────────


@dataclass
class InferenceMetrics:
    """Standardized inference metrics across all providers."""
    tokens_per_sec: float = 0.0
    first_token_ms: float = 0.0
    total_duration_ms: float = 0.0
    eval_count: int = 0
    prompt_eval_count: int = 0


@dataclass
class ProviderChatResponse:
    """Standardized chat response from any provider."""
    content: str
    model: str = ""
    metrics: InferenceMetrics = None  # type: ignore[assignment]
    done: bool = True
    finish_reason: str = "stop"

    def __post_init__(self):
        if self.metrics is None:
            self.metrics = InferenceMetrics()


@dataclass
class ProviderStreamChunk:
    """A single streaming chunk from any provider."""
    content: str = ""
    done: bool = False
    model: str = ""
    # Final chunk metrics
    metrics: Optional[InferenceMetrics] = None


@dataclass
class ProviderModelInfo:
    """Information about a model available in the provider."""
    name: str
    size_bytes: int = 0
    parameter_size: str = ""
    quantization: str = ""
    family: str = ""

    @property
    def size_gb(self) -> float:
        return round(self.size_bytes / (1024 ** 3), 2) if self.size_bytes else 0.0


@dataclass
class ProviderRunningModel:
    """A model currently loaded in the provider."""
    name: str
    vram_used_mb: int = 0
    ram_used_mb: int = 0
    expires_at: str = ""


# ── Base Provider ─────────────────────────────────────────────────────────────


class BaseProvider(abc.ABC):
    """
    Abstract base class for all model inference providers.

    Every provider must implement:
    - Health check
    - Model listing and availability
    - Model loading/unloading (VRAM management)
    - Chat inference (non-streaming and streaming)
    - Running model status (for VRAM monitoring)
    """

    def __init__(self, base_url: str, provider_name: str):
        self.base_url = base_url.rstrip("/")
        self.provider_name = provider_name

    # ── Health ────────────────────────────────────────────────────────────

    @abc.abstractmethod
    async def is_running(self) -> bool:
        """Check if the provider backend is reachable."""
        ...

    # ── Model Management ──────────────────────────────────────────────────

    @abc.abstractmethod
    async def list_models(self) -> list[ProviderModelInfo]:
        """List all models available in this provider."""
        ...

    @abc.abstractmethod
    async def model_exists(self, model_id: str) -> bool:
        """Check if a specific model is available."""
        ...

    @abc.abstractmethod
    async def load_model(self, model_id: str, keep_alive: str = "10m") -> bool:
        """Pre-warm a model into VRAM/memory."""
        ...

    @abc.abstractmethod
    async def unload_model(self, model_id: str) -> bool:
        """Evict a model from VRAM/memory."""
        ...

    @abc.abstractmethod
    async def running_models(self) -> list[ProviderRunningModel]:
        """List models currently loaded with VRAM usage."""
        ...

    # ── Inference ─────────────────────────────────────────────────────────

    @abc.abstractmethod
    async def chat(
        self,
        model_id: str,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        keep_alive: str = "10m",
    ) -> ProviderChatResponse:
        """Non-streaming chat completion."""
        ...

    @abc.abstractmethod
    async def chat_stream(
        self,
        model_id: str,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        keep_alive: str = "10m",
    ) -> AsyncIterator[ProviderStreamChunk]:
        """Streaming chat completion — yields chunks as they arrive."""
        ...
        # Make the type checker happy for async generators
        if False:
            yield  # pragma: no cover
