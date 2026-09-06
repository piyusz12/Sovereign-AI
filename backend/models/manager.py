from backend.models.registry import get_all_models
from backend.models.schemas import ModelStatus

# Simulated RTX 4060 laptop GPU constraints
MAX_VRAM_MB = 8192

def get_vram_usage() -> int:
    """Calculate currently used VRAM by loaded models."""
    usage = 0
    for model in get_all_models():
        if model.loaded:
            usage += model.vram_estimate_mb
    # Assume 500MB system overhead
    return usage + 500

def can_load_model(vram_required: int) -> bool:
    """Check if the system has enough VRAM to load a model."""
    current_usage = get_vram_usage()
    return (current_usage + vram_required) <= MAX_VRAM_MB

def load_model(model_id: str) -> bool:
    """
    Attempt to load a model.
    In a real system, this would call vLLM / Ollama API to load the model into memory.
    """
    from backend.models.registry import get_model, update_model_status
    
    model = get_model(model_id)
    if not model:
        return False
        
    if model.loaded:
        return True
        
    if can_load_model(model.vram_estimate_mb):
        update_model_status(model_id, status=ModelStatus.READY, loaded=True)
        return True
        
    # Insufficient VRAM
    update_model_status(model_id, status=ModelStatus.UNAVAILABLE, loaded=False, error="Insufficient VRAM")
    return False

def unload_model(model_id: str):
    """
    Unload a model from memory.
    """
    from backend.models.registry import update_model_status
    update_model_status(model_id, status=ModelStatus.READY, loaded=False)
