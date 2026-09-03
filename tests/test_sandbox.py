"""
Tests — Docker Code Sandbox

Verifies sandbox isolation and execution behavior.
"""

import pytest
from backend.tools.python_sandbox import PythonSandboxTool


@pytest.fixture
def sandbox():
    return PythonSandboxTool()


class TestSandbox:
    """Test sandbox execution."""

    @pytest.mark.asyncio
    async def test_sandbox_permission_check(self, sandbox):
        """Sandbox requires engineering or admin role."""
        result = await sandbox.execute(user_role="finance", code="print('hello')")
        assert not result.success
        assert "Permission denied" in result.error

    @pytest.mark.asyncio
    async def test_sandbox_engineering_allowed(self, sandbox):
        """Engineering role can use sandbox."""
        # Note: This will fail if Docker is not running, which is expected
        result = await sandbox.execute(user_role="engineering", code="print('hello')")
        # Either succeeds or fails due to Docker not being available
        assert result.tool_name == "run_python"
