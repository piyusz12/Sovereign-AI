"""
Sovereign AI Workbench — Agent Graph Nodes

Individual node functions for the LangGraph agent graph.
Each node transforms the AgentState.

Flow:
    START → understand → plan → select_tool → execute_tool →
    observe → verify → (retry/repair/output) → END
"""

from __future__ import annotations

import logging
from typing import Any

from backend.agent.state import AgentState

logger = logging.getLogger("sovereign.agent.nodes")


async def understand_node(state: AgentState) -> dict[str, Any]:
    """
    Understand the user's request and classify the task.
    Sets task_type, model_selected, and initial plan direction.
    """
    logger.info("NODE: understand — analyzing user request")

    user_request = state.get("user_request", "")

    # TODO Phase 11: Use actual task classifier + LLM for understanding
    return {
        "task_type": state.get("task_type", "reasoning"),
        "model_selected": state.get("model_selected", "qwen3-14b"),
        "iteration_count": 0,
        "errors": [],
        "tool_calls": [],
        "tool_results": [],
        "retrieved_context": [],
        "files_created": [],
        "sources_cited": [],
        "query_rewrites": [],
        "retrieval_attempts": 0,
        "code_fix_attempts": 0,
    }


async def plan_node(state: AgentState) -> dict[str, Any]:
    """
    Create an execution plan based on the understood request.
    The plan is a sequence of tool calls to execute.
    """
    logger.info("NODE: plan — creating execution plan")

    task_type = state.get("task_type", "reasoning")

    # TODO Phase 11: Use LLM to generate a dynamic plan
    # For now, use template plans based on task type
    plan_templates = {
        "reasoning": [
            {"step": "search_documents", "description": "Search internal knowledge base"},
            {"step": "analyze", "description": "Analyze retrieved context"},
            {"step": "respond", "description": "Generate response with citations"},
        ],
        "coding": [
            {"step": "understand_requirements", "description": "Parse coding requirements"},
            {"step": "generate_code", "description": "Generate code solution"},
            {"step": "execute_sandbox", "description": "Run in Docker sandbox"},
            {"step": "verify_output", "description": "Verify execution results"},
        ],
        "vision": [
            {"step": "analyze_image", "description": "Process image with vision model"},
            {"step": "search_context", "description": "Search related internal documents"},
            {"step": "respond", "description": "Generate response with visual findings"},
        ],
        "document_reasoning": [
            {"step": "ingest_document", "description": "Process uploaded document"},
            {"step": "search_documents", "description": "Retrieve relevant context"},
            {"step": "analyze", "description": "Analyze with reasoning model"},
            {"step": "generate_output", "description": "Create output document"},
        ],
    }

    plan = plan_templates.get(task_type, plan_templates["reasoning"])

    return {
        "plan": plan,
        "current_step": 0,
    }


async def select_tool_node(state: AgentState) -> dict[str, Any]:
    """
    Select the next tool to execute based on the current plan step.
    """
    logger.info("NODE: select_tool — choosing next action")

    plan = state.get("plan", [])
    current_step = state.get("current_step", 0)

    if current_step >= len(plan):
        return {"current_step": current_step}

    step = plan[current_step]
    logger.info("Selected step %d: %s", current_step, step.get("step", "unknown"))

    return {"current_step": current_step}


async def execute_tool_node(state: AgentState) -> dict[str, Any]:
    """
    Execute the selected tool. This is where actual work happens:
    - RAG retrieval
    - Code execution in Docker sandbox
    - Vision analysis
    - Document generation
    """
    logger.info("NODE: execute_tool — running tool")

    plan = state.get("plan", [])
    current_step = state.get("current_step", 0)
    tool_results = list(state.get("tool_results", []))

    if current_step >= len(plan):
        return {"tool_results": tool_results}

    step = plan[current_step]

    # TODO Phase 9-10: Implement actual tool execution
    result = {
        "step": step.get("step"),
        "status": "pending_implementation",
        "output": None,
    }
    tool_results.append(result)

    return {
        "tool_results": tool_results,
        "current_step": current_step + 1,
    }


async def observe_node(state: AgentState) -> dict[str, Any]:
    """
    Observe the results of tool execution.
    Check for errors, insufficient data, or success.
    """
    logger.info("NODE: observe — evaluating results")

    tool_results = state.get("tool_results", [])
    errors = list(state.get("errors", []))
    iteration_count = state.get("iteration_count", 0) + 1

    # Check for errors in the latest result
    if tool_results:
        latest = tool_results[-1]
        if latest.get("status") == "error":
            errors.append(f"Step '{latest.get('step')}' failed: {latest.get('error')}")

    return {
        "errors": errors,
        "iteration_count": iteration_count,
    }


async def verify_node(state: AgentState) -> dict[str, Any]:
    """
    Verify the quality of results.

    Three possible outcomes:
    1. VERIFIED — results are good, proceed to output
    2. RETRY — insufficient evidence, rewrite query and try again
    3. FAILED — errors detected, attempt repair

    After max_iterations or max_retrieval_attempts, fail-closed
    (refuse to fabricate an answer).
    """
    logger.info("NODE: verify — checking result quality")

    iteration_count = state.get("iteration_count", 0)
    max_iterations = state.get("max_iterations", 5)
    errors = state.get("errors", [])
    plan = state.get("plan", [])
    current_step = state.get("current_step", 0)

    # Safety: stop after max iterations
    if iteration_count >= max_iterations:
        return {
            "verification_status": "max_iterations_reached",
            "verification_details": f"Stopped after {max_iterations} iterations",
        }

    # If there are errors, attempt repair
    if errors:
        return {
            "verification_status": "failed",
            "verification_details": f"Errors detected: {'; '.join(errors[-3:])}",
        }

    # If we've completed all steps, verify the output
    if current_step >= len(plan):
        return {
            "verification_status": "verified",
            "verification_details": "All plan steps completed successfully",
        }

    # More steps to execute
    return {
        "verification_status": "in_progress",
        "verification_details": f"Step {current_step}/{len(plan)} completed",
    }


async def output_node(state: AgentState) -> dict[str, Any]:
    """
    Generate the final output response.
    Includes the answer, citations, and any generated files.
    """
    logger.info("NODE: output — generating final response")

    verification_status = state.get("verification_status", "unknown")

    if verification_status == "verified":
        response = "Task completed successfully."
    elif verification_status == "max_iterations_reached":
        response = (
            "I was unable to fully complete this task within the allowed iterations. "
            "Here is what I found so far."
        )
    else:
        response = (
            "I do not have sufficient internal evidence to provide a reliable answer. "
            "This is a fail-closed response to maintain data integrity."
        )

    return {
        "response": response,
    }


async def error_handler_node(state: AgentState) -> dict[str, Any]:
    """
    Handle errors by attempting repairs.
    For code errors: rewrite code based on stderr.
    For RAG errors: rewrite query and retry retrieval.
    """
    logger.info("NODE: error_handler — attempting repair")

    errors = state.get("errors", [])
    code_fix_attempts = state.get("code_fix_attempts", 0)

    # TODO Phase 11: Implement actual error repair logic
    return {
        "code_fix_attempts": code_fix_attempts + 1,
        "errors": [],  # Clear errors after handling
    }
