from typing import Dict, List, Optional
from backend.models.schemas import ModelInfo, ModelCapability, ModelStatus

# A static registry of available open-weight models
# In a real enterprise system, this could be backed by a database.
_MODELS_DB: Dict[str, ModelInfo] = {
    "reasoning-local": ModelInfo(
        id="reasoning-local",
        name="qwen3:14b",
        role="reasoning",
        capabilities=[ModelCapability.TEXT],
        context_length=8192,
        quantization="4-bit",
        vram_estimate_mb=7000,
        status=ModelStatus.READY,
        loaded=False,
    ),
    "coding-local": ModelInfo(
        id="coding-local",
        name="qwen2.5-coder:7b",
        role="coding",
        capabilities=[ModelCapability.TEXT, ModelCapability.CODE],
        context_length=8192,
        quantization="4-bit",
        vram_estimate_mb=4200,
        status=ModelStatus.READY,
        loaded=False,
        backend="ollama"
    ),
    "vision-local": ModelInfo(
        id="vision-local",
        name="qwen3-vl:8b",
        role="vision",
        capabilities=[ModelCapability.TEXT, ModelCapability.VISION],
        context_length=4096,
        quantization="4-bit",
        vram_estimate_mb=6800,
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
    """Get a specific model by ID."""
    return _MODELS_DB.get(model_id)

def update_model_status(model_id: str, status: ModelStatus, loaded: bool = False, latency_ms: Optional[float] = None, error: Optional[str] = None):
    """Update runtime telemetry for a model."""
    if model_id in _MODELS_DB:
        _MODELS_DB[model_id].status = status
        _MODELS_DB[model_id].loaded = loaded
        if latency_ms is not None:
            _MODELS_DB[model_id].latency_ms = latency_ms
        if error is not None:
            _MODELS_DB[model_id].last_error = error
