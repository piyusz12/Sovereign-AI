"""
PHASE 11 — Agent state.

Single source of truth for what flows through the LangGraph graph. Kept in
its own file because the RAG nodes (Phase 17), RBAC filter (Phase 18), and
document tools (Phase 12+) will all read/write this same object later —
better to nail the shape now than reshape it under five node functions.
"""

from __future__ import annotations

from typing import Any, List, Optional, TypedDict
import uuid

# In python 3.11+, NotRequired is in typing
try:
    from typing import NotRequired
except ImportError:
    from typing_extensions import NotRequired


class ToolResult(TypedDict):
    tool: str
    success: bool
    output: str
    error: str


class AgentState(TypedDict):
    # input
    session_id: str         # Trace execution ID for zero-egress telemetry
    user_request: str
    user_role: str          # RBAC role: "engineering", "admin", "operations", etc.

    # understand_goal
    task_type: str          # "coding" | "document_reasoning" | "vision" | "unsupported"
    task_type_reason: str

    # plan
    plan: List[str]

    # select_tool / execute_tool / observe
    current_step_index: int
    tool_results: List[ToolResult]

    # retrieval (Phase 17+, empty until RAG exists)
    retrieved_context: List[str]

    # verify / repair
    verification_status: str  # "complete" | "error" | "insufficient" | "unsupported"
    errors: List[str]
    attempts: int
    max_attempts: int

    # output
    files_created: List[str]
    final_answer: Optional[str]
    
    # telemetry
    duration_ms: NotRequired[float]


def new_state(
    user_request: str,
    *,
    user_role: str = "engineering",
    max_attempts: int = 3,
    session_id: Optional[str] = None,
) -> AgentState:
    """Factory so every entry point builds a fully-initialized state —
    LangGraph will not fill in missing keys for you."""
    return AgentState(
        session_id=session_id or str(uuid.uuid4()),
        user_request=user_request,
        user_role=user_role,
        task_type="",
        task_type_reason="",
        plan=[],
        current_step_index=0,
        tool_results=[],
        retrieved_context=[],
        verification_status="",
        errors=[],
        attempts=0,
        max_attempts=max_attempts,
        files_created=[],
        final_answer=None,
        duration_ms=0.0,
    )
