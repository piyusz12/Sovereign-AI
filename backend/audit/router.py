from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.audit.schemas import AuditEventResponse, AuditEvent
from backend.audit.service import audit_service
from backend.security.dependencies import require_permission

router = APIRouter(prefix="/audit", tags=["Audit Logging"])


@router.get("/events", response_model=AuditEventResponse)
async def get_audit_events(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    trace_id: Optional[str] = None,
    status: Optional[str] = None,
    _ = Depends(require_permission("audit.read"))
):
    """
    Retrieve audit events, optionally filtered.
    Requires 'audit.read' permission.
    """
    filters = {}
    if user_id:
        filters["user_id"] = user_id
    if action:
        filters["action"] = action
    if trace_id:
        filters["trace_id"] = trace_id
    if status:
        filters["status"] = status
        
    events = audit_service.get_events(limit=limit, offset=offset, **filters)
    # This is a naive total for prototype; ideally we'd query COUNT(*)
    return AuditEventResponse(events=events, total=len(events))


@router.get("/workflows/{trace_id}", response_model=AuditEventResponse)
async def get_workflow_trace(
    trace_id: str,
    _ = Depends(require_permission("audit.read"))
):
    """
    Retrieve all audit events for a specific workflow trace, ordered chronologically.
    Requires 'audit.read' permission.
    """
    # SQLite returns descending by default from our service, so we might want to reverse for chron order
    events = audit_service.get_events(limit=1000, trace_id=trace_id)
    events.reverse() # chronological
    return AuditEventResponse(events=events, total=len(events))
