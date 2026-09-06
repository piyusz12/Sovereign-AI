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
)
from backend.optimization.vram import vram_manager
from backend.optimization.hardware import current_hardware
from backend.optimization.scheduler import gpu_scheduler
from backend.optimization.telemetry import inference_telemetry
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
        "active_gpu_jobs": gpu_scheduler.active_jobs,
        "hardware_profile": {
            "name": current_hardware.name,
            "ram_mb": current_hardware.system_ram_mb
        },
        "gateway_health": gateway_health,
        "models": get_all_models()
    }


@router.get("/metrics")
async def inference_metrics() -> Dict[str, Any]:
    """Return local TTFT/ITL telemetry without exposing prompts or documents."""
    snapshot = inference_telemetry.snapshot()
    snapshot["scheduler"] = {
        "queue_depth": gpu_scheduler.queue_depth,
        "active_jobs": gpu_scheduler.active_jobs,
    }
    return snapshot

@router.get("/{model_id}", response_model=ModelInfo)
async def get_model_info(model_id: str):
    model = get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model

@router.post("/{model_id}/load")
async def api_load_model(model_id: str):
    """Load a model inside the async VRAM lifecycle manager."""
    from backend.optimization.model_manager import opt_model_manager

    if await opt_model_manager.ensure_loaded(model_id):
        return {"status": "success", "message": f"Model {model_id} loaded."}
    raise HTTPException(status_code=507, detail="Insufficient VRAM to load model.")

@router.post("/{model_id}/unload")
async def api_unload_model(model_id: str):
    from backend.optimization.model_manager import opt_model_manager

    model = get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    await opt_model_manager._unload_model(model)
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
