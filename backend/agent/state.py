"""
Sovereign AI Workbench — Agent State

TypedDict state definition for the LangGraph agent.
Carries all context through the cyclic agent execution graph.
"""

from __future__ import annotations

from typing import Any, Optional, TypedDict


class AgentState(TypedDict, total=False):
    """
    Complete state carried through the LangGraph agent execution.

    The agent graph uses cyclic state transitions:
    Understand → Plan → Select Tool → Execute → Observe → Verify → (retry/repair/output)
    """

    # ── User Input ─────────────────────────────────────────────────────────
    user_request: str
    user_role: str  # RBAC role

    # ── Classification ─────────────────────────────────────────────────────
    task_type: str
    model_selected: str
    classification_confidence: float

    # ── Planning ───────────────────────────────────────────────────────────
    plan: list[dict[str, Any]]  # Ordered list of planned steps
    current_step: int

    # ── Tool Execution ─────────────────────────────────────────────────────
    tool_calls: list[dict[str, Any]]  # History of tool calls
    tool_results: list[dict[str, Any]]  # Results from tools

    # ── RAG Context ────────────────────────────────────────────────────────
    retrieved_context: list[dict[str, Any]]  # Retrieved document chunks
    retrieval_scores: list[float]
    query_rewrites: list[str]  # Track query reformulations
    retrieval_attempts: int

    # ── Code Execution ─────────────────────────────────────────────────────
    generated_code: Optional[str]
    sandbox_stdout: Optional[str]
    sandbox_stderr: Optional[str]
    sandbox_exit_code: Optional[int]
    code_fix_attempts: int

    # ── Output ─────────────────────────────────────────────────────────────
    response: str  # Final response text
    files_created: list[str]  # Generated documents
    sources_cited: list[dict[str, Any]]  # Document citations

    # ── Verification ───────────────────────────────────────────────────────
    verification_status: str  # "verified", "failed", "insufficient_evidence"
    verification_details: str
    errors: list[str]

    # ── Metadata ───────────────────────────────────────────────────────────
    messages: list[dict[str, Any]]  # LLM message history
    iteration_count: int
    max_iterations: int  # Safety limit
