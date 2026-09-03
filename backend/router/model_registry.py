"""
Sovereign AI Workbench — Model Registry

Central registry of all available models. Tracks providers, quantization,
resource requirements, and which model is currently loaded on GPU.

CRITICAL: Only ONE heavy model can be loaded on the RTX 4060 8GB at a time.
The registry enforces this single-GPU discipline.

Phase 4: Now uses OllamaClient for real model lifecycle management.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from backend.router.ollama_client import ollama_client, OllamaClient

logger = logging.getLogger("sovereign.model_registry")


class ModelProvider(str, Enum):
    """Supported model serving backends."""
    OLLAMA = "ollama"
    VLLM = "vllm"
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

    # Runtime state
    loaded: bool = False
    vram_used_mb: int = 0


# ── Default Model Registry ────────────────────────────────────────────────────

DEFAULT_MODELS: dict[str, ModelConfig] = {
    "reasoning": ModelConfig(
        name="Qwen3-14B",
        provider=ModelProvider.OLLAMA,
        model_id="qwen3:14b",
        category=ModelCategory.REASONING,
        quantization="4-bit",
        context_length=32768,
        vram_required_mb=7000,
        is_heavy=True,
        base_url="http://localhost:11434",
    ),
    "coding": ModelConfig(
        name="Qwen2.5-Coder-7B",
        provider=ModelProvider.OLLAMA,
        model_id="qwen2.5-coder:7b",
        category=ModelCategory.CODING,
        quantization="4-bit",
        context_length=16384,
        vram_required_mb=5000,
        is_heavy=True,
        base_url="http://localhost:11434",
    ),
    "vision": ModelConfig(
        name="Qwen3-VL-8B",
        provider=ModelProvider.OLLAMA,
        model_id="qwen3-vl:8b",
        category=ModelCategory.VISION,
        quantization="4-bit",
        context_length=8192,
        vram_required_mb=6000,
        is_heavy=True,
        base_url="http://localhost:11434",
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

    Phase 4: Uses OllamaClient for real model lifecycle via Ollama REST API.
    """

    def __init__(
        self,
        models: Optional[dict[str, ModelConfig]] = None,
        client: Optional[OllamaClient] = None,
    ):
        self.models = models or {k: ModelConfig(**v.__dict__) for k, v in DEFAULT_MODELS.items()}
        self._active_heavy_model: Optional[str] = None
        self._ollama = client or ollama_client

    def get_model(self, category: str) -> Optional[ModelConfig]:
        """Get model config by category."""
        return self.models.get(category)

    def get_active_heavy_model(self) -> Optional[str]:
        """Return the currently loaded heavy model category."""
        return self._active_heavy_model

    async def ensure_model_available(self, category: str) -> bool:
        """
        Check if a model is pulled and available in Ollama.
        Logs a clear error if not found.

        Returns:
            True if model is available
        """
        model = self.models.get(category)
        if not model:
            logger.error("Unknown model category: %s", category)
            return False

        if model.provider != ModelProvider.OLLAMA:
            # Non-Ollama models — can't check availability yet
            return True

        exists = await self._ollama.model_exists(model.model_id)
        if not exists:
            logger.error(
                "Model '%s' (%s) is not pulled in Ollama. "
                "Run: ollama pull %s",
                model.name, model.model_id, model.model_id,
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

        # Load via Ollama API
        if model.provider == ModelProvider.OLLAMA:
            success = await self._ollama.load_model(
                model.model_id,
                keep_alive=model.keep_alive,
            )
            if not success:
                logger.warning(
                    "Ollama load_model returned failure for %s — "
                    "model may still work if already loaded",
                    model.model_id,
                )
        else:
            logger.info(
                "Provider %s does not support pre-warming — marking as loaded",
                model.provider.value,
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
        """Unload a model from GPU via Ollama API."""
        model = self.models.get(category)
        if not model:
            return

        if model.provider == ModelProvider.OLLAMA:
            await self._ollama.unload_model(model.model_id)

        model.loaded = False
        model.vram_used_mb = 0
        if self._active_heavy_model == category:
            self._active_heavy_model = None
        logger.info("Model %s unloaded", model.name)

    async def sync_with_ollama(self) -> None:
        """
        Reconcile registry state with what Ollama actually has loaded.
        Calls /api/ps to discover real loaded models and VRAM usage.
        """
        running = await self._ollama.ps()
        running_names = {m.name for m in running}

        # Reset all loaded states
        for model in self.models.values():
            model.loaded = False
            model.vram_used_mb = 0

        self._active_heavy_model = None

        # Match running models to registry entries
        for rm in running:
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

        # Log any running models not in our registry
        registry_ids = {m.model_id for m in self.models.values()}
        for rm in running:
            if not any(
                rm.name == rid or rm.name.startswith(rid.split(":")[0])
                for rid in registry_ids
            ):
                logger.warning(
                    "Ollama has model '%s' loaded but it's not in the registry",
                    rm.name,
                )

    async def _sync_vram_for_model(self, model: ModelConfig) -> None:
        """Update a single model's VRAM usage from Ollama ps."""
        running = await self._ollama.ps()
        for rm in running:
            if rm.name == model.model_id or rm.name.startswith(model.model_id.split(":")[0]):
                model.vram_used_mb = rm.vram_used_mb
                return
        # If not found in ps, use estimated VRAM
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
        Uses real VRAM data from Ollama ps.
        """
        total_vram = 8192  # RTX 4060 Laptop

        # Get real data from Ollama
        running = await self._ollama.ps()
        real_vram_used = sum(m.vram_used_mb for m in running)

        # Also track what our registry thinks
        registry_used = sum(m.vram_used_mb for m in self.models.values() if m.loaded)

        return {
            "gpu_model": "RTX 4060 Laptop",
            "total_vram_mb": total_vram,
            "used_vram_mb": real_vram_used if real_vram_used > 0 else registry_used,
            "available_vram_mb": total_vram - (real_vram_used or registry_used),
            "active_heavy_model": self._active_heavy_model,
            "ollama_loaded_models": [
                {"name": m.name, "vram_mb": m.vram_used_mb}
                for m in running
            ],
        }


# Global instance
model_registry = ModelRegistry()
