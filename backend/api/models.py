from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from backend.models import (
    get_all_models,
    get_model,
    route_task,
    get_vram_usage,
    RoutingRequest,
    RoutingResponse,
    ModelInfo,
    load_model,
    unload_model
)
from backend.optimization.vram import vram_manager
from backend.optimization.hardware import current_hardware
from backend.optimization.scheduler import gpu_scheduler
from backend.model_gateway import check_gateway_health

router = APIRouter(prefix="/models", tags=["models"])

@router.get("", response_model=List[ModelInfo])
async def list_models():
    """List all models in the registry."""
    return get_all_models()

@router.get("/status")
async def model_status() -> Dict[str, Any]:
    """Get overall system VRAM and model health (Phase 28 Optimizations)."""
    vram_state = vram_manager.get_state()
    gateway_health = await check_gateway_health()
    return {
        "vram_used_mb": vram_state.used_mb,
        "max_vram_mb": vram_state.total_mb,
        "vram_status": vram_state.status,
        "queue_depth": gpu_scheduler.queue_depth,
        "hardware_profile": {
            "name": current_hardware.name,
            "ram_mb": current_hardware.system_ram_mb
        },
        "gateway_health": gateway_health,
        "models": get_all_models()
    }

@router.get("/{model_id}", response_model=ModelInfo)
async def get_model_info(model_id: str):
    model = get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model

@router.post("/{model_id}/load")
async def api_load_model(model_id: str):
    """Load model into memory (sync wrapper)."""
    if load_model(model_id):
        # We also attempt to load it on the backend provider
        # (This would be backgrounded or async in production)
        return {"status": "success", "message": f"Model {model_id} loaded."}
    raise HTTPException(status_code=507, detail="Insufficient VRAM to load model.")

@router.post("/{model_id}/unload")
async def api_unload_model(model_id: str):
    unload_model(model_id)
    return {"status": "success", "message": f"Model {model_id} unloaded."}

@router.post("/route", response_model=RoutingResponse)
async def api_route_task(request: RoutingRequest):
    """
    Core of Phase 27: Select the best model for the task.
    """
    try:
        response = route_task(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
