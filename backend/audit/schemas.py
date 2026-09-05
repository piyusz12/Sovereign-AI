from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class AuditEvent(BaseModel):
    """
    Standard schema for all audit events in the Sovereign AI Workbench.
    """
    event_id: str
    trace_id: Optional[str] = None
    timestamp: datetime
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    project_id: Optional[str] = None
    role: Optional[str] = None
    permission: Optional[str] = None
    decision: Optional[str] = None
    model: Optional[str] = None
    tool: Optional[str] = None
    sandbox_job_id: Optional[str] = None
    source_ip: Optional[str] = None
    destination: Optional[str] = None
    status: str
    error_code: Optional[str] = None
    metadata_info: dict[str, Any] = Field(default_factory=dict)


class AuditEventResponse(BaseModel):
    """
    Response model for the audit API.
    """
    events: list[AuditEvent]
    total: int
