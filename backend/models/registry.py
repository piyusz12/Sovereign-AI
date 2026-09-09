from typing import Dict, List, Optional
from backend.models.schemas import ModelInfo, ModelCapability, ModelStatus
from backend.settings import settings

# A static registry of available open-weight models
# In a real enterprise system, this could be backed by a database.
_MODELS_DB: Dict[str, ModelInfo] = {
    "reasoning-local": ModelInfo(
        id="reasoning-local",
        name=settings.ollama_reasoning_model,
        role="reasoning",
        capabilities=[ModelCapability.TEXT],
        context_length=8192,
        quantization="4-bit",
        vram_estimate_mb=5200,
        status=ModelStatus.READY,
        loaded=False,
    ),
    "coding-local": ModelInfo(
        id="coding-local",
        name=settings.ollama_coding_model,
        role="coding",
        capabilities=[ModelCapability.TEXT, ModelCapability.CODE],
        context_length=8192,
        quantization="4-bit",
        vram_estimate_mb=4700,
        status=ModelStatus.READY,
        loaded=False,
        backend="ollama"
    ),
    "vision-local": ModelInfo(
        id="vision-local",
        name=settings.ollama_vision_model,
        role="vision",
        capabilities=[ModelCapability.TEXT, ModelCapability.VISION],
        context_length=4096,
        quantization="4-bit",
        vram_estimate_mb=7800,
        status=ModelStatus.READY,
        loaded=False
    ),
    "embedding-local": ModelInfo(
        id="embedding-local",
        name="qwen3-embedding:0.6b",
        version="v1",
        role="embedding",
        capabilities=[ModelCapability.EMBEDDING],
        context_length=8192,
        vram_estimate_mb=800,
        status=ModelStatus.READY,
        loaded=False,
        backend="infinity"
    ),
    "reranker-local": ModelInfo(
        id="reranker-local",
        name="BAAI/bge-reranker-base",
        version="v1",
        role="reranking",
        capabilities=[ModelCapability.RERANKER],
        context_length=8192,
        vram_estimate_mb=600,
        status=ModelStatus.READY,
        loaded=False,
        backend="infinity"
    )
}

def get_all_models() -> List[ModelInfo]:
    """Return all models in the registry."""
    return list(_MODELS_DB.values())

def get_model(model_id: str) -> Optional[ModelInfo]:
    """Get a specific model by ID, name, role, or alias."""
    if not model_id:
        return None
    if model_id in _MODELS_DB:
        return _MODELS_DB[model_id]

    norm = model_id.strip().lower()
    for m in _MODELS_DB.values():
        if m.id.lower() == norm or m.name.lower() == norm or m.role.lower() == norm:
            return m
        # Strip '-local' or ':version' for loose matching
        id_stem = m.id.replace("-local", "").lower()
        if id_stem == norm or id_stem == norm.replace("-local", ""):
            return m
        name_stem = m.name.replace(":", "-").lower()
        if norm.replace(":", "-") in name_stem or name_stem in norm.replace(":", "-"):
            return m
    return None

def update_model_status(model_id: str, status: ModelStatus, loaded: bool = False, latency_ms: Optional[float] = None, error: Optional[str] = None):
    """Update runtime telemetry for a model."""
    m = get_model(model_id)
    if m:
        m.status = status
        m.loaded = loaded
        if latency_ms is not None:
            m.latency_ms = latency_ms
        if error is not None:
            m.last_error = error
