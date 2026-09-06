"""
Sovereign AI Workbench — Security Dashboard API
"""

from fastapi import APIRouter
from backend.security.engine import policy_engine

router = APIRouter(prefix="/security", tags=["security"])

@router.get("/dashboard")
async def get_security_dashboard():
    """Return security status and audit events for the dashboard."""
    events = policy_engine.get_audit_events()
    blocked = [e for e in events if e.get("decision") == "DENY"]
    pending = [e for e in events if e.get("decision") == "REQUIRE_APPROVAL"]
    
    return {
        "status": "secure",
        "controls": {
            "Authentication": True,
            "RBAC": True,
            "Policy Engine": True,
            "RAG Access Control": True,
            "Sandbox Isolation": True,
            "Network Policy": True,
            "Audit Logging": True,
        },
        "stats": {
            "active_threats": 0,
            "blocked": len(blocked),
            "pending_approvals": len(pending),
        },
        "recent_events": events[-10:]  # Return last 10 events
    }
