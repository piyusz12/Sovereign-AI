from enum import Enum
from pydantic import BaseModel
from typing import List, Optional

class TaskType(str, Enum):
    GENERAL_CHAT = "GENERAL_CHAT"
    DOCUMENT_ANALYSIS = "DOCUMENT_ANALYSIS"
    CODING = "CODING"
    VISION = "VISION"
    DATA_ANALYSIS = "DATA_ANALYSIS"
    RAG_SEARCH = "RAG_SEARCH"
    SUMMARIZATION = "SUMMARIZATION"
    PLANNING = "PLANNING"
    EMBEDDING = "EMBEDDING"
    RERANKING = "RERANKING"

class ModelCapability(str, Enum):
    TEXT = "text"
    CODE = "code"
    VISION = "vision"
    EMBEDDING = "embedding"
    RERANKER = "reranker"

class ModelStatus(str, Enum):
    READY = "READY"
    UNAVAILABLE = "UNAVAILABLE"
    LOADING = "LOADING"

class ModelInfo(BaseModel):
    id: str
    name: str
    version: str = "v1"
    role: str
    capabilities: List[ModelCapability]
    context_length: int
    quantization: Optional[str] = None
    vram_estimate_mb: int
    enabled: bool = True
    backend: str = "ollama"
    
    # Runtime status
    status: ModelStatus = ModelStatus.UNAVAILABLE
    latency_ms: Optional[float] = None
    last_error: Optional[str] = None
    loaded: bool = False

class RoutingRequest(BaseModel):
    task_type: TaskType
    required_capabilities: Optional[List[ModelCapability]] = None
    trace_id: Optional[str] = None

class RoutingResponse(BaseModel):
    selected_model: str
    reason: str
    local: bool
