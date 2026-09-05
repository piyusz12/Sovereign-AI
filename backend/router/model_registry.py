"""
Sovereign AI Workbench — Model Registry

Central registry of all available models. Tracks providers, quantization,
resource requirements, and which model is currently loaded on GPU.

CRITICAL: Only ONE heavy model can be loaded on the RTX 4060 8GB at a time.
The registry enforces this single-GPU discipline.

Phase 5: Uses provider abstraction — registry is now backend-agnostic.
         Works with Ollama, vLLM, or any future provider through BaseProvider.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from backend.router.providers.base import BaseProvider
from backend.router.providers.factory import get_provider

logger = logging.getLogger("sovereign.model_registry")


class ModelProvider(str, Enum):
    """Supported model serving backends."""
    OLLAMA = "ollama"
    VLLM = "vllm"
    LITELLM = "litellm"
    INFINITY = "infinity"
    LOCAL = "local"


class ModelCategory(str, Enum):
    """Model specialization categories."""
    REASONING = "reasoning"
    CODING = "coding"
    VISION = "vision"
    EMBEDDING = "embedding"
    RERANKER = "reranker"


@dataclass
class ModelConfig:
    """Configuration for a single model."""
    name: str
    provider: ModelProvider
    model_id: str  # Provider-specific model identifier
    category: ModelCategory
    quantization: str = "4-bit"
    context_length: int = 8192
    vram_required_mb: int = 6000
    is_heavy: bool = True  # If True, only one can be loaded at a time
    base_url: str = "http://localhost:11434"
    api_format: str = "openai"  # openai-compatible API format
    keep_alive: str = "10m"  # How long Ollama keeps model loaded
    system_prompt: str = ""  # Category-specific system prompt

    # Runtime state
    loaded: bool = False
    vram_used_mb: int = 0


# ── Default System Prompts ────────────────────────────────────────────────────

_REASONING_SYSTEM_PROMPT = (
    "You are a Sovereign AI assistant operating entirely on local hardware. "
    "You have access to internal enterprise documents, code execution, and "
    "document generation tools. You must never reference or attempt to access "
    "external services. All your knowledge comes from locally stored documents "
    "and your training data. When you lack internal evidence, say so clearly "
    "rather than fabricating information."
)

# Import coding prompt from the coding module (avoid circular import at module level)
def _get_coding_system_prompt() -> str:
    from backend.router.coding import CODING_SYSTEM_PROMPT
    return CODING_SYSTEM_PROMPT

# Import vision prompt from the vision module (avoid circular import at module level)
def _get_vision_system_prompt() -> str:
    from backend.router.vision import VISION_SYSTEM_PROMPT
    return VISION_SYSTEM_PROMPT


# ── Default Model Registry ────────────────────────────────────────────────────

DEFAULT_MODELS: dict[str, ModelConfig] = {
    "reasoning": ModelConfig(
        name="Qwen3-14B (LiteLLM)",
        provider=ModelProvider.LITELLM,
        model_id="sovereign-reasoning",
        category=ModelCategory.REASONING,
        quantization="4-bit",
        context_length=32768,
        vram_required_mb=7000,
        is_heavy=True,
        base_url="http://localhost:4000",
        system_prompt=_REASONING_SYSTEM_PROMPT,
    ),
    "coding": ModelConfig(
        name="Qwen2.5-Coder-7B (LiteLLM)",
        provider=ModelProvider.LITELLM,
        model_id="sovereign-coding",
        category=ModelCategory.CODING,
        quantization="4-bit",
        context_length=16384,
        vram_required_mb=5000,
        is_heavy=True,
        base_url="http://localhost:4000",
        system_prompt="",  # Populated at runtime from coding module
    ),
    "vision": ModelConfig(
        name="Qwen3-VL-8B (LiteLLM)",
        provider=ModelProvider.LITELLM,
        model_id="sovereign-vision",
        category=ModelCategory.VISION,
        quantization="4-bit",
        context_length=8192,
        vram_required_mb=6000,
        is_heavy=True,
        base_url="http://localhost:4000",
        system_prompt="",  # Populated at runtime from vision module
    ),
    "embedding": ModelConfig(
        name="Qwen3-Embedding-0.6B",
        provider=ModelProvider.OLLAMA,
        model_id="qwen3-embedding:0.6b",
        category=ModelCategory.EMBEDDING,
        quantization="fp16",
        context_length=8192,
        vram_required_mb=800,
        is_heavy=False,  # Small enough to coexist
        base_url="http://localhost:11434",
    ),
    "reranker": ModelConfig(
        name="Qwen3-Reranker-0.6B",
        provider=ModelProvider.OLLAMA,
        model_id="qwen3-reranker:0.6b",
        category=ModelCategory.RERANKER,
        quantization="fp16",
        context_length=8192,
        vram_required_mb=800,
        is_heavy=False,
        base_url="http://localhost:11434",
    ),
}


class ModelRegistry:
    """
    Manages available models and enforces single-GPU discipline.

    Only one heavy model (reasoning/coding/vision) can be loaded at a time.
    Lightweight models (embedding/reranker) can coexist.

    Phase 5: Uses provider abstraction — delegates lifecycle to the correct
    BaseProvider for each model's configured provider.
    """

    def __init__(
        self,
        models: Optional[dict[str, ModelConfig]] = None,
    ):
        self.models = models or {k: ModelConfig(**v.__dict__) for k, v in DEFAULT_MODELS.items()}
        self._active_heavy_model: Optional[str] = None

    def _get_provider(self, model: ModelConfig) -> BaseProvider:
        """Get the appropriate provider for a model."""
        return get_provider(model.provider.value, model.base_url)

    def get_model(self, category: str) -> Optional[ModelConfig]:
        """Get model config by category."""
        return self.models.get(category)

    def get_active_heavy_model(self) -> Optional[str]:
        """Return the currently loaded heavy model category."""
        return self._active_heavy_model

    async def ensure_model_available(self, category: str) -> bool:
        """
        Check if a model is available in its provider.
        Logs a clear error if not found.

        Returns:
            True if model is available
        """
        model = self.models.get(category)
        if not model:
            logger.error("Unknown model category: %s", category)
            return False

        provider = self._get_provider(model)
        exists = await provider.model_exists(model.model_id)
        if not exists:
            logger.error(
                "Model '%s' (%s) is not available in %s. "
                "For Ollama, run: ollama pull %s",
                model.name, model.model_id, model.provider.value, model.model_id,
            )
        return exists

    async def load_model(self, category: str) -> ModelConfig:
        """
        Load a model, unloading the current heavy model if necessary.
        For Ollama models, this pre-warms the model into VRAM.

        Returns the loaded model config.
        """
        model = self.models.get(category)
        if not model:
            raise ValueError(f"Unknown model category: {category}")

        # If this heavy model is already active, skip reload
        if model.is_heavy and self._active_heavy_model == category and model.loaded:
            logger.debug("Model %s already loaded, skipping", model.name)
            return model

        # Unload current heavy model if switching to a different one
        if model.is_heavy and self._active_heavy_model and self._active_heavy_model != category:
            logger.info(
                "Unloading %s to make room for %s",
                self._active_heavy_model,
                category,
            )
            await self.unload_model(self._active_heavy_model)

        # Load via provider API
        provider = self._get_provider(model)
        success = await provider.load_model(
            model.model_id,
            keep_alive=model.keep_alive,
        )
        if not success:
            logger.warning(
                "%s load_model returned failure for %s — "
                "model may still work if already loaded",
                model.provider.value, model.model_id,
            )

        model.loaded = True
        if model.is_heavy:
            self._active_heavy_model = category

        # Sync VRAM usage from Ollama
        await self._sync_vram_for_model(model)

        logger.info(
            "Model %s (%s) loaded on GPU — VRAM: %d MB",
            model.name, category, model.vram_used_mb,
        )
        return model

    async def unload_model(self, category: str) -> None:
        """Unload a model from GPU via its provider."""
        model = self.models.get(category)
        if not model:
            return

        provider = self._get_provider(model)
        await provider.unload_model(model.model_id)

        model.loaded = False
        model.vram_used_mb = 0
        if self._active_heavy_model == category:
            self._active_heavy_model = None
        logger.info("Model %s unloaded", model.name)

    async def sync_with_providers(self) -> None:
        """
        Reconcile registry state with what providers actually have loaded.
        Queries each provider's running models and updates VRAM usage.
        """
        # Reset all loaded states
        for model in self.models.values():
            model.loaded = False
            model.vram_used_mb = 0
        self._active_heavy_model = None

        # Query each unique provider
        queried_providers: set[str] = set()
        all_running = []

        for model in self.models.values():
            provider_key = f"{model.provider.value}:{model.base_url}"
            if provider_key in queried_providers:
                continue
            queried_providers.add(provider_key)

            provider = self._get_provider(model)
            running = await provider.running_models()
            all_running.extend(running)

        # Match running models to registry entries
        for rm in all_running:
            for category, model in self.models.items():
                if rm.name == model.model_id or rm.name.startswith(model.model_id.split(":")[0]):
                    model.loaded = True
                    model.vram_used_mb = rm.vram_used_mb
                    if model.is_heavy:
                        self._active_heavy_model = category
                    logger.info(
                        "Synced: %s is loaded — VRAM: %d MB",
                        model.name, model.vram_used_mb,
                    )
                    break

        # Log unmatched running models
        registry_ids = {m.model_id for m in self.models.values()}
        for rm in all_running:
            if not any(
                rm.name == rid or rm.name.startswith(rid.split(":")[0])
                for rid in registry_ids
            ):
                logger.warning(
                    "Provider has model '%s' loaded but it's not in the registry",
                    rm.name,
                )

    # Backward-compatible alias
    sync_with_ollama = sync_with_providers

    async def _sync_vram_for_model(self, model: ModelConfig) -> None:
        """Update a single model's VRAM usage from its provider."""
        provider = self._get_provider(model)
        running = await provider.running_models()
        for rm in running:
            if rm.name == model.model_id or rm.name.startswith(model.model_id.split(":")[0]):
                model.vram_used_mb = rm.vram_used_mb
                return
        # If not found, use estimated VRAM
        model.vram_used_mb = model.vram_required_mb

    def list_models(self) -> list[dict]:
        """List all models with their status."""
        return [
            {
                "category": cat,
                "name": m.name,
                "provider": m.provider.value,
                "model_id": m.model_id,
                "loaded": m.loaded,
                "quantization": m.quantization,
                "vram_required_mb": m.vram_required_mb,
                "vram_used_mb": m.vram_used_mb,
                "is_heavy": m.is_heavy,
                "context_length": m.context_length,
            }
            for cat, m in self.models.items()
        ]

    async def get_gpu_status(self) -> dict:
        """
        Return current GPU allocation status.
        Queries all providers for real VRAM data.
        """
        total_vram = 8192  # RTX 4060 Laptop

        # Get real data from all providers
        all_running = []
        queried: set[str] = set()
        for model in self.models.values():
            key = f"{model.provider.value}:{model.base_url}"
            if key in queried:
                continue
            queried.add(key)
            provider = self._get_provider(model)
            running = await provider.running_models()
            all_running.extend(running)

        real_vram_used = sum(m.vram_used_mb for m in all_running)
        registry_used = sum(m.vram_used_mb for m in self.models.values() if m.loaded)

        return {
            "gpu_model": "RTX 4060 Laptop",
            "total_vram_mb": total_vram,
            "used_vram_mb": real_vram_used if real_vram_used > 0 else registry_used,
            "available_vram_mb": total_vram - (real_vram_used or registry_used),
            "active_heavy_model": self._active_heavy_model,
            "loaded_models": [
                {"name": m.name, "vram_mb": m.vram_used_mb}
                for m in all_running
            ],
        }


# Global instance
model_registry = ModelRegistry()
