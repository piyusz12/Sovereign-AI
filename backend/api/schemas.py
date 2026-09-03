"""
Sovereign AI Workbench — Pydantic Schemas

Request/response models for all API endpoints.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ── Enums ──────────────────────────────────────────────────────────────────────


class TaskType(str, Enum):
    """Types of tasks the system can handle."""
    REASONING = "reasoning"
    CODING = "coding"
    VISION = "vision"
    DOCUMENT_REASONING = "document_reasoning"
    DATA_ANALYSIS = "data_analysis"
    GENERAL = "general"


class ModelName(str, Enum):
    """Available models in the system."""
    QWEN3_14B = "qwen3-14b"
    QWEN25_CODER_7B = "qwen2.5-coder-7b"
    QWEN3_VL_8B = "qwen3-vl-8b"


class UserRole(str, Enum):
    """RBAC user roles."""
    ADMIN = "admin"
    ENGINEERING = "engineering"
    FINANCE = "finance"
    PROCUREMENT = "procurement"
    HR = "hr"
    OPERATIONS = "operations"


class ToolAction(str, Enum):
    """Available tool actions for the agent."""
    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    LIST_FILES = "list_files"
    CALCULATE = "calculate"
    SEARCH_DOCUMENTS = "search_documents"
    RUN_PYTHON = "run_python"
    CREATE_DOCX = "create_docx"
    CREATE_XLSX = "create_xlsx"
    CREATE_PPTX = "create_pptx"
    INSPECT_IMAGE = "inspect_image"


# ── Request Models ─────────────────────────────────────────────────────────────


class ChatRequest(BaseModel):
    """Chat/query request from the user."""
    message: str = Field(..., min_length=1, max_length=10000)
    task_type: Optional[TaskType] = None  # Auto-classified if not provided
    model: Optional[ModelName] = None  # Auto-routed if not provided
    context: Optional[list[str]] = None  # Additional context
    user_role: UserRole = UserRole.ENGINEERING
    stream: bool = False


class UploadRequest(BaseModel):
    """Document upload metadata."""
    filename: str
    document_type: Optional[str] = None
    department: Optional[str] = None
    access_level: UserRole = UserRole.ENGINEERING
    description: Optional[str] = None


class SearchRequest(BaseModel):
    """RAG search request."""
    query: str = Field(..., min_length=1, max_length=5000)
    top_k: int = Field(default=5, ge=1, le=50)
    rerank: bool = True
    user_role: UserRole = UserRole.ENGINEERING
    department_filter: Optional[str] = None


class GenerateRequest(BaseModel):
    """Document generation request."""
    request_type: str = Field(..., description="Type: approval_note, report, analysis")
    source_data: dict[str, Any] = Field(default_factory=dict)
    output_format: str = Field(default="docx", pattern="^(docx|xlsx|pptx)$")
    template: Optional[str] = None


class CodeExecutionRequest(BaseModel):
    """Code execution request for the sandbox."""
    code: str = Field(..., min_length=1)
    language: str = Field(default="python")
    timeout_seconds: int = Field(default=30, ge=1, le=120)


# ── Response Models ────────────────────────────────────────────────────────────


class RouteInfo(BaseModel):
    """Information about how a request was routed."""
    task_type: TaskType
    model: ModelName
    reason: str


class SourceDocument(BaseModel):
    """A source document citation."""
    document_id: str
    title: str
    page: Optional[int] = None
    relevance_score: float
    snippet: str


class ToolResult(BaseModel):
    """Result from a tool execution."""
    tool: ToolAction
    success: bool
    result: Any
    error: Optional[str] = None
    duration_ms: float


class ChatResponse(BaseModel):
    """Response to a chat/query request."""
    response: str
    route: RouteInfo
    sources: list[SourceDocument] = Field(default_factory=list)
    tools_used: list[ToolResult] = Field(default_factory=list)
    files_created: list[str] = Field(default_factory=list)
    sovereign: bool = True
    request_id: str
    duration_ms: float


class UploadResponse(BaseModel):
    """Response after document upload and processing."""
    document_id: str
    filename: str
    pages: int
    chunks: int
    status: str
    processing_time_ms: float


class SearchResponse(BaseModel):
    """Response from a RAG search."""
    results: list[SourceDocument]
    query: str
    total_found: int
    reranked: bool


class GenerateResponse(BaseModel):
    """Response from document generation."""
    filename: str
    file_path: str
    format: str
    pages: Optional[int] = None


class CodeExecutionResponse(BaseModel):
    """Response from sandbox code execution."""
    stdout: str
    stderr: str
    exit_code: int
    execution_time_ms: float
    files_created: list[str] = Field(default_factory=list)


class ModelStatus(BaseModel):
    """Status of a model."""
    name: str
    provider: str
    loaded: bool
    vram_mb: Optional[int] = None
    quantization: str = "4-bit"


class SystemStatus(BaseModel):
    """Full system status."""
    status: str
    sovereign: bool
    models: list[ModelStatus]
    services: dict[str, str]
    uptime_seconds: float


class AuditEntry(BaseModel):
    """Audit log entry."""
    timestamp: datetime
    user: str
    task_id: str
    model: Optional[str] = None
    tool: Optional[str] = None
    documents: list[str] = Field(default_factory=list)
    result: str
    duration_ms: float
