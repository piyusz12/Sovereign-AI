"""
Sovereign AI Workbench — LangGraph Agent

Defines the cyclic agent execution graph.

Architecture:
    START → understand → plan → select_tool → execute_tool →
    observe → verify
        ├── in_progress → select_tool (loop)
        ├── failed → error_handler → select_tool (retry)
        ├── max_iterations → output (fail-closed)
        └── verified → output → END
"""

from __future__ import annotations

import logging
from typing import Any

from backend.agent.state import AgentState
from backend.agent.nodes import (
    understand_node,
    plan_node,
    select_tool_node,
    execute_tool_node,
    observe_node,
    verify_node,
    output_node,
    error_handler_node,
)

logger = logging.getLogger("sovereign.agent")


def _should_continue(state: AgentState) -> str:
    """
    Routing function after the verify node.
    Determines the next step based on verification status.
    """
    status = state.get("verification_status", "unknown")

    if status == "verified":
        return "output"
    elif status == "failed":
        # Check if we've exceeded repair attempts
        if state.get("code_fix_attempts", 0) >= 3:
            return "output"
        return "error_handler"
    elif status == "in_progress":
        return "select_tool"
    else:
        # max_iterations_reached or unknown
        return "output"


def create_agent_graph():
    """
    Create the LangGraph agent graph.

    Returns a compiled graph that can be invoked with an initial AgentState.

    NOTE: This function requires langgraph to be installed.
    During Phase 0-3 scaffold, this returns a placeholder.
    """
    try:
        from langgraph.graph import StateGraph, END

        # Build the graph
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("understand", understand_node)
        workflow.add_node("plan", plan_node)
        workflow.add_node("select_tool", select_tool_node)
        workflow.add_node("execute_tool", execute_tool_node)
        workflow.add_node("observe", observe_node)
        workflow.add_node("verify", verify_node)
        workflow.add_node("output", output_node)
        workflow.add_node("error_handler", error_handler_node)

        # Define edges
        workflow.set_entry_point("understand")
        workflow.add_edge("understand", "plan")
        workflow.add_edge("plan", "select_tool")
        workflow.add_edge("select_tool", "execute_tool")
        workflow.add_edge("execute_tool", "observe")
        workflow.add_edge("observe", "verify")

        # Conditional routing after verification
        workflow.add_conditional_edges(
            "verify",
            _should_continue,
            {
                "output": "output",
                "error_handler": "error_handler",
                "select_tool": "select_tool",
            },
        )

        # Error handler loops back to retry
        workflow.add_edge("error_handler", "select_tool")

        # Output is terminal
        workflow.add_edge("output", END)

        # Compile
        graph = workflow.compile()
        logger.info("LangGraph agent compiled successfully")
        return graph

    except ImportError:
        logger.warning(
            "langgraph not installed — agent graph not available. "
            "Install with: pip install langgraph"
        )
        return None


async def run_agent(
    user_request: str,
    user_role: str = "engineering",
    task_type: str | None = None,
    max_iterations: int = 5,
) -> dict[str, Any]:
    """
    Run the agent on a user request.

    Args:
        user_request: The user's request
        user_role: RBAC role for document access
        task_type: Optional forced task type
        max_iterations: Maximum execution iterations

    Returns:
        Final agent state as a dict
    """
    graph = create_agent_graph()

    if graph is None:
        return {
            "response": "[Agent not available — langgraph not installed]",
            "verification_status": "unavailable",
        }

    initial_state: AgentState = {
        "user_request": user_request,
        "user_role": user_role,
        "task_type": task_type or "reasoning",
        "max_iterations": max_iterations,
        "messages": [{"role": "user", "content": user_request}],
    }

    result = await graph.ainvoke(initial_state)
    return dict(result)
