"""
Tests — LangGraph Agent

Verifies agent state, graph structure, and execution behavior.
"""

import pytest
from backend.agent.state import AgentState
from backend.agent.nodes import understand_node, plan_node, verify_node


class TestAgentState:
    """Test agent state structure."""

    def test_state_creation(self):
        """AgentState can be created with minimal fields."""
        state: AgentState = {
            "user_request": "Test request",
            "user_role": "engineering",
        }
        assert state["user_request"] == "Test request"

    def test_state_with_all_fields(self):
        """AgentState accepts all defined fields."""
        state: AgentState = {
            "user_request": "Analyze this report",
            "user_role": "engineering",
            "task_type": "document_reasoning",
            "model_selected": "qwen3-14b",
            "plan": [],
            "tool_results": [],
            "retrieved_context": [],
            "errors": [],
            "files_created": [],
            "verification_status": "pending",
            "max_iterations": 5,
        }
        assert state["max_iterations"] == 5


class TestAgentNodes:
    """Test individual agent graph nodes."""

    @pytest.mark.asyncio
    async def test_understand_node(self):
        """Understand node initializes state correctly."""
        state: AgentState = {"user_request": "Test", "user_role": "engineering"}
        result = await understand_node(state)
        assert "errors" in result
        assert result["errors"] == []

    @pytest.mark.asyncio
    async def test_plan_node_reasoning(self):
        """Plan node creates a plan for reasoning tasks."""
        state: AgentState = {"task_type": "reasoning"}
        result = await plan_node(state)
        assert "plan" in result
        assert len(result["plan"]) > 0

    @pytest.mark.asyncio
    async def test_plan_node_coding(self):
        """Plan node creates a coding plan with sandbox step."""
        state: AgentState = {"task_type": "coding"}
        result = await plan_node(state)
        steps = [s["step"] for s in result["plan"]]
        assert "execute_sandbox" in steps

    @pytest.mark.asyncio
    async def test_verify_max_iterations(self):
        """Verify node stops at max iterations."""
        state: AgentState = {
            "iteration_count": 5,
            "max_iterations": 5,
            "errors": [],
            "plan": [],
            "current_step": 0,
        }
        result = await verify_node(state)
        assert result["verification_status"] == "max_iterations_reached"
