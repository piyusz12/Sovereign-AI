from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from backend.security.dependencies import get_optional_current_user
from backend.security.rbac import rbac_enforcer
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
from backend.optimization.cpu_engine import cpu_engine
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
    cpu_metrics = cpu_engine.get_compute_metrics()
    return {
        "vram_used_mb": vram_state.used_mb,
        "max_vram_mb": vram_state.total_mb,
        "vram_status": vram_state.status,
        "queue_depth": gpu_scheduler.queue_depth,
        "active_gpu_jobs": gpu_scheduler.active_jobs,
        "hardware_profile": {
            "name": current_hardware.name,
            "ram_mb": current_hardware.system_ram_mb,
            "cpu_cores": current_hardware.cpu_cores,
            "cpu_threads": current_hardware.cpu_threads,
            "cpu_model": current_hardware.cpu_model,
            "simd_avx2": current_hardware.simd_avx2_supported,
            "compute_mode": current_hardware.compute_mode,
        },
        "cpu_compute": cpu_metrics,
        "gateway_health": gateway_health,
        "models": get_all_models(),
    }


@router.get("/metrics")
async def inference_metrics() -> Dict[str, Any]:
    """Return local TTFT/ITL telemetry without exposing prompts or documents."""
    snapshot = inference_telemetry.snapshot()
    snapshot["scheduler"] = {
        "queue_depth": gpu_scheduler.queue_depth,
        "active_jobs": gpu_scheduler.active_jobs,
    }
    snapshot["cpu_compute"] = cpu_engine.get_compute_metrics()
    return snapshot

@router.get("/{model_id}", response_model=ModelInfo)
async def get_model_info(model_id: str):
    model = get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model

@router.post("/{model_id}/load")
async def api_load_model(
    model_id: str,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user),
):
    """Load a model inside the async VRAM lifecycle manager with RBAC validation."""
    if current_user and not rbac_enforcer.can_manage_models(current_user.get("role", "")):
        raise HTTPException(
            status_code=403,
            detail=f"Role '{current_user.get('role')}' is not authorized to load models. Requires Admin or Engineering.",
        )

    model = get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found in registry.")

    from backend.optimization.model_manager import opt_model_manager

    if await opt_model_manager.ensure_loaded(model.id):
        try:
            from backend.cpp_bridge import cpp_core
            cpp_core.record_model_loaded(model.id, model.vram_estimate_mb)
        except Exception:
            pass
        return {"status": "success", "message": f"Model {model.id} loaded.", "model_id": model.id}
    raise HTTPException(status_code=507, detail=f"Insufficient VRAM to load model {model.id}.")

@router.post("/{model_id}/unload")
async def api_unload_model(
    model_id: str,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user),
):
    """Unload a model from VRAM with RBAC validation."""
    if current_user and not rbac_enforcer.can_manage_models(current_user.get("role", "")):
        raise HTTPException(
            status_code=403,
            detail=f"Role '{current_user.get('role')}' is not authorized to unload models. Requires Admin or Engineering.",
        )

    model = get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found in registry.")

    from backend.optimization.model_manager import opt_model_manager

    await opt_model_manager._unload_model(model)
    try:
        from backend.cpp_bridge import cpp_core
        cpp_core.record_model_unloaded(model.id)
    except Exception:
        pass
    return {"status": "success", "message": f"Model {model.id} unloaded.", "model_id": model.id}

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
