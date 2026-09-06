from typing import Optional
import logging

from backend.models.schemas import RoutingRequest, RoutingResponse, ModelCapability, TaskType, ModelStatus
from backend.models.registry import get_all_models
from backend.models.manager import can_load_model, load_model
from backend.audit.service import audit_service

logger = logging.getLogger(__name__)

def determine_required_capabilities(task_type: TaskType) -> list[ModelCapability]:
    """Map a task type to the required model capabilities."""
    if task_type == TaskType.CODING:
        return [ModelCapability.TEXT, ModelCapability.CODE]
    elif task_type == TaskType.VISION:
        return [ModelCapability.TEXT, ModelCapability.VISION]
    elif task_type == TaskType.DOCUMENT_ANALYSIS or task_type == TaskType.GENERAL_CHAT:
        return [ModelCapability.TEXT]
    elif task_type == TaskType.RAG_SEARCH:
        return [ModelCapability.EMBEDDING]
    return [ModelCapability.TEXT]

def route_task(request: RoutingRequest) -> RoutingResponse:
    """
    Selects the best available model for a given task.
    Enforces VRAM constraints and logs the selection to the audit trail.
    """
    required_caps = request.required_capabilities or determine_required_capabilities(request.task_type)
    
    available_models = get_all_models()
    
    # Filter by capability
    candidates = []
    for m in available_models:
        if not m.enabled:
            continue
            
        # Ensure model has ALL required capabilities
        has_all_caps = all(cap in m.capabilities for cap in required_caps)
        if has_all_caps:
            candidates.append(m)
            
    if not candidates:
        raise ValueError(f"No enabled model found with capabilities: {required_caps}")
        
    # Sort candidates (prefer loaded models, then lower VRAM to save space)
    candidates.sort(key=lambda x: (not x.loaded, x.vram_estimate_mb))
    
    selected_model = None
    reason = ""
    
    for candidate in candidates:
        if candidate.loaded:
            selected_model = candidate
            reason = f"Model {candidate.id} already loaded and supports required capabilities."
            break
        elif load_model(candidate.id):
            selected_model = candidate
            reason = f"Dynamically loaded {candidate.id} to satisfy {request.task_type.value}."
            break
                
    if not selected_model:
        raise RuntimeError("Insufficient VRAM to load any candidate model for this task.")
        
    response = RoutingResponse(
        selected_model=selected_model.id,
        reason=reason,
        local=True
    )
    
    # Audit logging for Sovereignty
    audit_service.log(
        action=f"route_task({request.task_type.value})",
        status="success",
        user_id="system",
        resource_id=selected_model.id,
        resource_type="model",
        metadata={
            "trace_id": request.trace_id,
            "reason": reason,
            "local": True
        }
    )
    
    return response
