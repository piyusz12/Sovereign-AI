import pytest

from backend.coding_agent import agent
from backend.coding_agent.planner import create_plan
from backend.coding_agent.schemas import TaskPlan


@pytest.mark.asyncio
async def test_create_plan_rejects_unusable_model_response(monkeypatch):
    async def fake_generate_code(*args, **kwargs):
        return type("Generation", (), {"code": "I cannot make a plan"})()

    monkeypatch.setattr("backend.coding_agent.planner.generate_code", fake_generate_code)

    with pytest.raises(RuntimeError, match="unusable plan"):
        await create_plan("add a feature", ["app.py"])


@pytest.mark.asyncio
async def test_agent_stops_when_patch_is_not_applied(tmp_path, monkeypatch):
    (tmp_path / "app.py").write_text("value = 1\n", encoding="utf-8")

    async def fake_plan(task, files):
        return TaskPlan(steps=["edit app"], affected_files=["app.py"])

    async def fake_patch(*args, **kwargs):
        return "Error: Could not find the exact search_text block in app.py."

    monkeypatch.setattr(agent, "create_plan", fake_plan)
    monkeypatch.setattr(agent, "generate_patch", fake_patch)

    result = await agent.run_coding_agent(str(tmp_path), "change the value")

    assert result["status"] == "error"
    assert "Could not find" in result["error"]


@pytest.mark.asyncio
async def test_agent_executes_planned_patch_and_verifies_tests(tmp_path, monkeypatch):
    (tmp_path / "app.py").write_text("value = 1\n", encoding="utf-8")

    async def fake_plan(task, files):
        return TaskPlan(steps=["edit app"], affected_files=["app.py"])

    async def fake_patch(repo_path, task, file_path, context, error_log=""):
        return "Successfully updated app.py"

    monkeypatch.setattr(agent, "create_plan", fake_plan)
    monkeypatch.setattr(agent, "generate_patch", fake_patch)
    monkeypatch.setattr(
        agent,
        "run_tests_in_sandbox",
        lambda repo_path, command: {"success": True, "output": "1 passed", "error": ""},
    )

    result = await agent.run_coding_agent(str(tmp_path), "change the value")

    assert result["status"] == "success"
    assert result["output"] == "1 passed"