import asyncio
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from backend.sovereignty.schemas import SovereigntyStatus
from backend.sovereignty.service import sovereignty_service


router = APIRouter(prefix="/sovereignty", tags=["Sovereignty"])

@router.get("/status", response_model=SovereigntyStatus)
async def get_sovereignty_status(
    # Require read access, could use specific roles like admin, engineer, or auditor
    # user = Depends(require_role(["admin", "engineer", "auditor"]))
):
    """
    Get the current overall sovereignty status.
    """
    return sovereignty_service.status

@router.get("/stream")
async def stream_sovereignty_events(request: Request):
    """
    Server-Sent Events (SSE) stream for real-time sovereignty dashboard.
    """
    async def event_generator():
        q = sovereignty_service.subscribe()
        try:
            while True:
                if await request.is_disconnected():
                    break
                message = await q.get()
                yield message
        finally:
            sovereignty_service.unsubscribe(q)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
