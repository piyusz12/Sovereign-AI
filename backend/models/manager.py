"""
Sovereign AI Workbench — Model Lifecycle Manager (Phase 26)

Manages VRAM, model loading/unloading, and concurrency limits to 
prevent OOM crashes on resource-constrained hardware (e.g. 8GB RTX 4060).
"""

import logging
import asyncio

logger = logging.getLogger("sovereign.models.manager")

class ModelLifecycleManager:
    def __init__(self, max_vram_gb: float = 8.0):
        self.max_vram_gb = max_vram_gb
        self.active_models: dict[str, str] = {}
        self._lock = asyncio.Lock()

    async def load(self, model_name: str, model_type: str, required_vram_gb: float = 4.0) -> bool:
        """Attempt to load a model, gracefully unloading others if needed."""
        async with self._lock:
            if model_name in self.active_models:
                logger.debug(f"Model {model_name} is already loaded.")
                return True

            current_vram = len(self.active_models) * 4.0  # Naive estimation for now
            if current_vram + required_vram_gb > self.max_vram_gb:
                logger.warning(f"VRAM limit reached. Unloading models to fit {model_name}...")
                await self._unload_all()

            logger.info(f"Loading {model_type} model: {model_name}...")
            # Actual loading logic would go here (e.g., calling provider.load_model)
            self.active_models[model_name] = model_type
            return True

    async def unload(self, model_name: str) -> bool:
        """Unload a specific model."""
        async with self._lock:
            if model_name in self.active_models:
                logger.info(f"Unloading model: {model_name}")
                # Actual unloading logic would go here
                del self.active_models[model_name]
                return True
            return False

    async def _unload_all(self):
        """Unload all active models to free VRAM."""
        models = list(self.active_models.keys())
        for m in models:
            logger.info(f"Unloading model: {m}")
            del self.active_models[m]

    async def health_check(self) -> dict:
        """Return status of all loaded models."""
        return {
            "status": "healthy",
            "active_models": self.active_models,
            "estimated_vram_usage_gb": len(self.active_models) * 4.0
        }

# Global singleton
model_manager = ModelLifecycleManager()
