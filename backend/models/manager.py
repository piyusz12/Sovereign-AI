from backend.optimization.vram import vram_manager
from backend.optimization.model_manager import sync_ensure_loaded
from backend.models.registry import update_model_status
from backend.models.schemas import ModelStatus

def get_vram_usage() -> int:
    """Calculate currently used VRAM (Phase 28: now pulls from advanced tracker)."""
    return vram_manager.get_state().used_mb

def can_load_model(vram_required: int) -> bool:
    """Check if the system has enough VRAM."""
    return vram_manager.can_allocate(vram_required)

def load_model(model_id: str) -> bool:
    """
    Attempt to load a model synchronously (Phase 28 optimization logic).
    """
    return sync_ensure_loaded(model_id)

def unload_model(model_id: str):
    """
    Unload a model from memory (Phase 28).
    """
    from backend.optimization.model_manager import opt_model_manager
    import asyncio
    
    # Fire and forget if we're calling this synchronously just to force an unload
    try:
        loop = asyncio.get_event_loop()
        from backend.models.registry import get_model
        m = get_model(model_id)
        if m and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                pool.submit(asyncio.run, opt_model_manager._unload_model(m))
        elif m:
            loop.run_until_complete(opt_model_manager._unload_model(m))
    except Exception:
        pass
