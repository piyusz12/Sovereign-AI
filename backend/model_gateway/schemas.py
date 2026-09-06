from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class ChatMessage(BaseModel):
    role: str
    content: str

class GatewayInferenceRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: float = 0.7
    max_tokens: int = 4096
    stream: bool = False
    timeout: float = 120.0
    trace_id: Optional[str] = None
    # Local runtimes such as Ollama accept "json" or a JSON schema here. It
    # prevents expensive application-level retries for malformed tool payloads.
    response_format: Optional[str | Dict[str, Any]] = None

class InferenceMetadata(BaseModel):
    request_id: str
    model: str
    provider: str
    latency_ms: float
    output_tokens: int
    prompt_tokens: int
    status: str
    finish_reason: str = "stop"

class GatewayInferenceResponse(BaseModel):
    content: str
    metadata: InferenceMetadata

class GatewayStreamChunk(BaseModel):
    content: str
    done: bool
    metadata: Optional[InferenceMetadata] = None

class GatewayEmbeddingRequest(BaseModel):
    model: str
    input: List[str]
    timeout: float = 60.0

class GatewayEmbeddingResponse(BaseModel):
    embeddings: List[List[float]]
    metadata: InferenceMetadata

class GatewayRerankRequest(BaseModel):
    model: str
    query: str
    documents: List[str]
    timeout: float = 60.0

class GatewayRerankResponse(BaseModel):
    scores: List[float]
    metadata: InferenceMetadata
