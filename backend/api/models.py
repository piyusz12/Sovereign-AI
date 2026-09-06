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
    unload_model,
    get_provider
)

router = APIRouter(prefix="/models", tags=["models"])

@router.get("", response_model=List[ModelInfo])
async def list_models():
    """List all models in the registry."""
    return get_all_models()

@router.get("/status")
async def model_status() -> Dict[str, Any]:
    """Get overall system VRAM and model health."""
    return {
        "vram_used_mb": get_vram_usage(),
        "max_vram_mb": 8192,
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
