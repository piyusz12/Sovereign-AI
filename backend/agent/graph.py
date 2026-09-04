"""
PHASE 11 — LangGraph agent.

Implements the cycle from the architecture doc:

    START -> Understand Goal -> Plan -> Select Tool -> Execute Tool
          -> Observe -> Verify
                          |-- insufficient --> Plan (retry, re-plan)
                          |-- error --------> Repair --> Execute Tool
                          |-- complete -----> Output
                          |-- unsupported --> Output (fails gracefully)
    Output -> END

As of Phase 11, only the "coding" task_type has a real tool behind it
(Phases 8-9's generate/execute/repair loop). Other task types route
correctly through the whole graph and fail with a clear, structured
reason instead of a crash or a hallucinated answer — that's intentional:
the graph's shape should not have to change when RAG (Phase 17) and
vision (Phase 19) tools are added, only the tool registry does.

Run:
    python -m backend.agent.graph "write a function that reverses a string"
"""

from __future__ import annotations

import sys
import time
import logging
from typing import Literal

logger = logging.getLogger("sovereign.agent.graph")

from langgraph.graph import END, StateGraph

from backend.agent.reasoning_service import classify_task, make_plan, verify_result
from backend.agent.state import AgentState, new_state
from backend.agent.tools_registry import get_tool_for_task_type

# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------


def node_understand_goal(state: AgentState) -> dict:
    logger.info("[%s] Node: understand_goal", state.get("session_id", "unknown"))
    result = classify_task(state["user_request"])
    return {"task_type": result.task_type, "task_type_reason": result.reason}


def node_plan(state: AgentState) -> dict:
    logger.info("[%s] Node: plan", state.get("session_id", "unknown"))
    steps = make_plan(state["user_request"], state["task_type"])
    return {"plan": steps}


def node_select_tool(state: AgentState) -> dict:
    # Selection is currently a 1:1 mapping from task_type (see
    # tools_registry). This node exists as its own step so that later,
    # when a task_type can resolve to more than one candidate tool, the
    # decision logic has a home that isn't buried inside execute_tool.
    _ = get_tool_for_task_type(state["task_type"])
    return {
        "task_type_reason": state.get("task_type_reason", "")
        + f" | selected tool for '{state['task_type']}'"
    }


def node_execute_tool(state: AgentState) -> dict:
    from backend.security.rbac import rbac_enforcer
    from backend.security.audit import audit_log

    logger.info("[%s] Node: execute_tool (tool: %s)", state.get("session_id", "unknown"), state.get("task_type"))
    
    task_type = state["task_type"]
    user_role = state["user_role"]
    
    # Map task_type to required permission
    required_permission = f"tool.{task_type}"
    if task_type == "coding":
        required_permission = "agent.execute_code"
    elif task_type == "vision":
        required_permission = "ai.vision"
    elif task_type == "document_reasoning":
        required_permission = "rag.search"
        
    if not rbac_enforcer.has_permission(user_role, required_permission):
        # Log audit and fail
        audit_log.log_event(
            event_type="agent_tool_denied",
            user=user_role,
            result="DENIED",
            details={"required_permission": required_permission, "task_type": task_type},
        )
        return {
            "tool_results": state["tool_results"] + [{
                "tool": task_type,
                "success": False,
                "output": "",
                "error": f"Role '{user_role}' is not authorized to use {task_type} (requires {required_permission}).",
            }],
            "attempts": state["attempts"] + 1,
        }

    tool_fn = get_tool_for_task_type(task_type)
    
    # Pass high-level errors from previous attempts as context
    context = "\n".join(state["errors"]) if state["errors"] else ""
    execution = tool_fn(state["user_request"], context)
    
    tool_result = {
        "tool": execution.tool_name,
        "success": execution.success,
        "output": execution.output,
        "error": execution.error,
    }
    return {
        "tool_results": state["tool_results"] + [tool_result],
        "attempts": state["attempts"] + 1,
    }


def node_observe(state: AgentState) -> dict:
    if not state["tool_results"]:
        return {}
    last = state["tool_results"][-1]
    if last["error"]:
        return {"errors": state["errors"] + [last["error"]]}
    return {}


def node_verify(state: AgentState) -> dict:
    if not state["tool_results"]:
        return {"verification_status": "error"}

    last = state["tool_results"][-1]

    if last["tool"].startswith("unsupported:"):
        return {"verification_status": "unsupported"}

    status = verify_result(state["user_request"], last["output"], last["error"])
    return {"verification_status": status}


def node_repair(state: AgentState) -> dict:
    # No state change needed here — attempts is already incremented in
    # execute_tool. High-level verification errors are logged into state["errors"]
    # by node_observe, and automatically passed as `context` to the next
    # tool_fn execution in node_execute_tool.
    return {}


def node_output(state: AgentState) -> dict:
    last = state["tool_results"][-1] if state["tool_results"] else None

    if state["verification_status"] == "complete" and last:
        answer = f"Task completed via {last['tool']}.\n\n{last['output']}"
    elif state["verification_status"] == "unsupported" and last:
        answer = f"Could not complete this request: {last['error']}"
    else:
        answer = (
            "Could not produce a verified result after "
            f"{state['attempts']} attempt(s). Last error: "
            f"{state['errors'][-1] if state['errors'] else 'unknown'}"
        )

    return {"final_answer": answer}


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

VerifyRoute = Literal["repair", "plan", "output"]


def decide_after_verify(state: AgentState) -> VerifyRoute:
    status = state["verification_status"]

    if status == "complete":
        return "output"

    if status == "unsupported":
        return "output"

    attempts_left = state["attempts"] < state["max_attempts"]

    if status == "error" and attempts_left:
        return "repair"

    if status == "insufficient" and attempts_left:
        return "plan"

    # Out of attempts, whatever the status — fail closed, don't loop forever.
    return "output"


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------


def build_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("understand_goal", node_understand_goal)
    workflow.add_node("plan", node_plan)
    workflow.add_node("select_tool", node_select_tool)
    workflow.add_node("execute_tool", node_execute_tool)
    workflow.add_node("observe", node_observe)
    workflow.add_node("verify", node_verify)
    workflow.add_node("repair", node_repair)
    workflow.add_node("output", node_output)

    workflow.set_entry_point("understand_goal")

    workflow.add_edge("understand_goal", "plan")
    workflow.add_edge("plan", "select_tool")
    workflow.add_edge("select_tool", "execute_tool")
    workflow.add_edge("execute_tool", "observe")
    workflow.add_edge("observe", "verify")

    workflow.add_conditional_edges(
        "verify",
        decide_after_verify,
        {"repair": "repair", "plan": "plan", "output": "output"},
    )

    workflow.add_edge("repair", "execute_tool")
    workflow.add_edge("output", END)

    return workflow.compile()


_GRAPH = None


def get_graph():
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = build_graph()
    return _GRAPH


def run_agent(
    user_request: str,
    *,
    user_role: str = "engineering",
    max_attempts: int = 3,
    session_id: str | None = None,
) -> AgentState:
    """Synchronous entry point for the agent workflow."""
    graph = get_graph()
    start = time.time()
    initial_state = new_state(
        user_request,
        user_role=user_role,
        max_attempts=max_attempts,
        session_id=session_id,
    )
    result = graph.invoke(initial_state)
    result["duration_ms"] = (time.time() - start) * 1000
    logger.info("[%s] Agent execution finished in %.2fms", result.get("session_id"), result["duration_ms"])
    return result


async def arun_agent(
    user_request: str,
    *,
    user_role: str = "engineering",
    max_attempts: int = 3,
    session_id: str | None = None,
) -> AgentState:
    """Asynchronous entry point for FastAPI routes and async callers."""
    graph = get_graph()
    start = time.time()
    initial_state = new_state(
        user_request,
        user_role=user_role,
        max_attempts=max_attempts,
        session_id=session_id,
    )
    result = await graph.ainvoke(initial_state)
    result["duration_ms"] = (time.time() - start) * 1000
    logger.info("[%s] Async agent execution finished in %.2fms", result.get("session_id"), result["duration_ms"])
    return result


if __name__ == "__main__":
    request = " ".join(sys.argv[1:]) or "write a function that reverses a string"
    final_state = run_agent(request)
    print("task_type:", final_state["task_type"], "-", final_state["task_type_reason"])
    print("plan:", final_state["plan"])
    print("attempts:", final_state["attempts"])
    print("verification_status:", final_state["verification_status"])
    print("--- final answer ---")
    print(final_state["final_answer"])
