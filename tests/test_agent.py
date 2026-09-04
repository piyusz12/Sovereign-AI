"""
Tests — Phase 11 LangGraph Agent Architecture

Comprehensive test suite for AgentState, ReasoningService, ToolsRegistry,
LangGraph cyclic routing, and node transformations.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from backend.agent.graph import (
    decide_after_verify,
    get_graph,
    node_execute_tool,
    node_observe,
    node_output,
    node_plan,
    node_repair,
    node_select_tool,
    node_understand_goal,
    node_verify,
    run_agent,
)
from backend.agent.reasoning_service import (
    ClassificationResult,
    ReasoningServiceError,
    _clean_markdown_fences,
    _extract_json,
    classify_task,
    make_plan,
    verify_result,
)
from backend.agent.state import AgentState, new_state
from backend.agent.tools_registry import (
    ToolExecution,
    get_tool_for_task_type,
    run_async_safely,
)


class TestAgentState:
    """Test state initialization and schema integrity."""

    def test_new_state_initializes_all_required_keys(self):
        state = new_state("Write a quicksort in Python")
        assert state["user_request"] == "Write a quicksort in Python"
        assert state["user_role"] == "engineering"
        assert state["task_type"] == ""
        assert state["task_type_reason"] == ""
        assert state["plan"] == []
        assert state["current_step_index"] == 0
        assert state["tool_results"] == []
        assert state["retrieved_context"] == []
        assert state["verification_status"] == ""
        assert state["errors"] == []
        assert state["attempts"] == 0
        assert state["max_attempts"] == 3
        assert state["files_created"] == []
        assert state["final_answer"] is None

    def test_new_state_custom_parameters(self):
        state = new_state("Inspect boiler", user_role="operations", max_attempts=5)
        assert state["user_role"] == "operations"
        assert state["max_attempts"] == 5


class TestReasoningService:
    """Test Qwen3-14B reasoning service parsing and fallbacks."""

    def test_clean_markdown_fences(self):
        raw = "```json\n{\"steps\": [\"step 1\"]}\n```"
        assert _clean_markdown_fences(raw) == '{"steps": ["step 1"]}'

        raw2 = "```\n{\"key\": \"val\"}\n```"
        assert _clean_markdown_fences(raw2) == '{"key": "val"}'

    def test_extract_json_success(self):
        text = "Here is the result: {\"task_type\": \"coding\", \"reason\": \"python task\"} extra text"
        data = _extract_json(text)
        assert data["task_type"] == "coding"
        assert data["reason"] == "python task"

    def test_extract_json_no_object(self):
        with pytest.raises(ReasoningServiceError, match="No JSON object found"):
            _extract_json("Plain text with no curly braces at all.")

    def test_extract_json_malformed(self):
        with pytest.raises(ReasoningServiceError, match="Malformed JSON"):
            _extract_json("Broken json: {key: val}")

    @patch("backend.agent.reasoning_service._chat")
    def test_classify_task_mocked(self, mock_chat):
        mock_chat.return_value = '{"task_type": "coding", "reason": "user asked for code"}'
        result = classify_task("write a script")
        assert isinstance(result, ClassificationResult)
        assert result.task_type == "coding"
        assert result.reason == "user asked for code"

    @patch("backend.agent.reasoning_service._chat")
    def test_classify_task_unrecognized_defaults_to_general(self, mock_chat):
        mock_chat.return_value = '{"task_type": "quantum_teleportation", "reason": "unrecognized"}'
        result = classify_task("something obscure")
        assert result.task_type == "general_reasoning"

    @patch("backend.agent.reasoning_service._chat")
    def test_make_plan_mocked(self, mock_chat):
        mock_chat.return_value = '{"steps": ["Write test", "Write implementation", "Verify"]}'
        steps = make_plan("test prompt", "coding")
        assert len(steps) == 3
        assert steps[0] == "Write test"

    @patch("backend.agent.reasoning_service._chat")
    def test_verify_result_mocked(self, mock_chat):
        mock_chat.return_value = '{"status": "complete", "reason": "All checks passed"}'
        status = verify_result("reverse a string", "olleh", "")
        assert status == "complete"

        mock_chat.return_value = '{"status": "error", "reason": "Traceback found"}'
        status = verify_result("reverse a string", "", "IndexError")
        assert status == "error"


class TestToolsRegistry:
    """Test minimal Phase 11 tool registry and execution wrappers."""

    def test_unsupported_task_returns_clean_tool_execution(self):
        tool_fn = get_tool_for_task_type("unsupported_type")
        execution = tool_fn("test request")
        assert isinstance(execution, ToolExecution)
        assert execution.success is False
        assert execution.tool_name == "unsupported:unsupported_type"
        assert "No tool is implemented yet" in execution.error

    @patch("backend.agent.tools_registry.generate_and_verify")
    def test_coding_tool_mocked(self, mock_gen_verify):
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.stdout = "hello\n"
        mock_result.stderr = ""

        async def _mock_coro(req):
            return mock_result

        mock_gen_verify.side_effect = _mock_coro

        tool_fn = get_tool_for_task_type("coding")
        execution = tool_fn("print hello")
        assert execution.success is True
        assert execution.tool_name == "python_sandbox"
        assert execution.output == "hello\n"


class TestAgentGraph:
    """Test LangGraph graph construction, node steps, and conditional routing."""

    def test_get_graph_compilation(self):
        graph = get_graph()
        assert graph is not None

    def test_decide_after_verify_routing(self):
        # Complete -> Output
        s1 = new_state("test")
        s1["verification_status"] = "complete"
        assert decide_after_verify(s1) == "output"

        # Unsupported -> Output
        s2 = new_state("test")
        s2["verification_status"] = "unsupported"
        assert decide_after_verify(s2) == "output"

        # Error with attempts remaining -> Repair
        s3 = new_state("test", max_attempts=3)
        s3["verification_status"] = "error"
        s3["attempts"] = 1
        assert decide_after_verify(s3) == "repair"

        # Error with attempts exhausted -> Output (fail closed)
        s4 = new_state("test", max_attempts=3)
        s4["verification_status"] = "error"
        s4["attempts"] = 3
        assert decide_after_verify(s4) == "output"

        # Insufficient with attempts remaining -> Plan
        s5 = new_state("test", max_attempts=3)
        s5["verification_status"] = "insufficient"
        s5["attempts"] = 1
        assert decide_after_verify(s5) == "plan"

    def test_individual_node_transformations(self):
        state = new_state("test request")
        state["task_type"] = "general_reasoning"
        state["task_type_reason"] = "general inquiry"

        # Select tool
        sel_update = node_select_tool(state)
        assert "selected tool for 'general_reasoning'" in sel_update["task_type_reason"]

        # Execute tool
        exec_update = node_execute_tool(state)
        assert len(exec_update["tool_results"]) == 1
        assert exec_update["attempts"] == 1
        state["tool_results"] = exec_update["tool_results"]
        state["attempts"] = exec_update["attempts"]

        # Observe
        obs_update = node_observe(state)
        assert "errors" in obs_update

        # Verify unsupported
        state["errors"] = obs_update["errors"]
        ver_update = node_verify(state)
        assert ver_update["verification_status"] == "unsupported"
        state["verification_status"] = ver_update["verification_status"]

        # Output
        out_update = node_output(state)
        assert "Could not complete this request" in out_update["final_answer"]

    @patch("backend.agent.graph.classify_task")
    @patch("backend.agent.graph.make_plan")
    def test_end_to_end_agent_execution_unsupported(self, mock_plan, mock_classify):
        mock_classify.return_value = ClassificationResult(
            task_type="vision",
            reason="image inspection requested",
        )
        mock_plan.return_value = ["Select camera", "Inspect diagram"]

        final_state = run_agent("Inspect this diagram")
        assert final_state["task_type"] == "vision"
        assert len(final_state["plan"]) == 2
        assert final_state["verification_status"] == "unsupported"
        assert "Could not complete this request" in final_state["final_answer"]
