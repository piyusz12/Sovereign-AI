import logging
import asyncio
from typing import List, Optional
from backend.models.registry import get_all_models, get_model, update_model_status
from backend.models.schemas import ModelStatus, ModelInfo
from backend.optimization.vram import vram_manager


logger = logging.getLogger(__name__)

class OptimizationModelManager:
    """
    Hardware-aware model lifecycle manager for RTX 4060 constraint.
    """
    
    def __init__(self):
        # We classify embedding/reranking as lightweight models that should be resident
        self.resident_roles = {"embedding", "reranker"}
        self.lock = asyncio.Lock()

    async def _unload_model(self, model: ModelInfo):
        from backend.model_gateway import model_gateway
        logger.info(f"Unloading model {model.id} to free VRAM")
        success = await model_gateway.unload_model(model.id)
        if success:
            update_model_status(model.id, status=ModelStatus.READY, loaded=False)
            vram_manager.release(model.id)
        return success

    async def _load_model(self, model: ModelInfo) -> bool:
        from backend.model_gateway import model_gateway
        logger.info(f"Loading model {model.id} into VRAM")
        success = await model_gateway.load_model(model.id)
        if success:
            update_model_status(model.id, status=ModelStatus.READY, loaded=True)
            vram_manager.allocate(model.id, model.vram_estimate_mb)
        return success

    async def ensure_loaded(self, target_model_id: str) -> bool:
        """
        Ensures a model is loaded. If there's insufficient VRAM, applies 
        eviction policies (unloads non-resident heavy models) until it fits.
        """
        async with self.lock:
            target = get_model(target_model_id)
            if not target:
                return False
                
            if target.loaded:
                return True
                
            # Check if it fits currently
            if vram_manager.can_allocate(target.vram_estimate_mb):
                return await self._load_model(target)
                
            # Eviction policy: unload any loaded heavy models that aren't the target
            # For SIH Demo, we only expect ONE heavy model active at a time (Reasoning OR Coding OR Vision)
            available_models = get_all_models()
            for m in available_models:
                if m.loaded and m.id != target.id and m.role not in self.resident_roles:
                    await self._unload_model(m)
                    # Check if it fits now
                    if vram_manager.can_allocate(target.vram_estimate_mb):
                        return await self._load_model(target)

            # If we still can't fit it, we fail gracefully
            logger.error(f"Cannot load {target.id}: Insufficient VRAM even after eviction.")
            return False

# Global instance
opt_model_manager = OptimizationModelManager()

# We need to bridge this with the sync load_model/unload_model from the previous phase 
# which didn't actually do async loading cleanly. Let's provide a sync bridge for now, 
# although we should migrate to async routing.

def sync_ensure_loaded(model_id: str) -> bool:
    """Synchronous bridge for dynamic loading."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we are in an event loop (e.g. FastAPI worker), we shouldn't run this synchronously blocking 
            # if we can avoid it, but for compatibility with sync routers, we can use a thread or run_coroutine_threadsafe
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(asyncio.run, opt_model_manager.ensure_loaded(model_id)).result()
        else:
            return loop.run_until_complete(opt_model_manager.ensure_loaded(model_id))
    except Exception as e:
        logger.error(f"Failed to sync load {model_id}: {e}")
        return False
