"""
Sovereign AI Workbench — Tool Registry

The central registry and permission layer for all agent tools.
Enforces Role-Based Access Control (RBAC) before executing any tool.

Architecture:
    LLM ↓ Tool request ↓ ToolRegistry (verifies RBAC) ↓ Tool Execution ↓ Result
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from backend.tools.base import BaseTool, ToolResult
from backend.security.audit import audit_logger

logger = logging.getLogger("sovereign.tools.registry")


class ToolError(RuntimeError):
    pass


class ToolRegistry:
    """
    Manages available tools and enforces execution permissions.
    """

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool into the system."""
        if tool.name in self._tools:
            logger.warning(f"Tool {tool.name} is already registered. Overwriting.")
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")

    def get_tool(self, name: str) -> BaseTool:
        """Retrieve a tool by name."""
        if name not in self._tools:
            raise ToolError(f"Unknown tool requested: {name}")
        return self._tools[name]

    def list_tools(self) -> list[dict[str, Any]]:
        """List all available tools and their descriptions."""
        return [
            {
                "name": t.name,
                "description": t.description,
            }
            for t in self._tools.values()
        ]

    async def execute_tool(
        self,
        name: str,
        user_role: str,
        user_id: str,
        task_id: str,
        **kwargs,
    ) -> ToolResult:
        """
        Execute a tool safely, enforcing RBAC permissions and audit logging.
        """
        try:
            tool = self.get_tool(name)
        except ToolError as e:
            # Audit log unauthorized or missing tool attempt
            audit_logger.log_tool_execution(
                user_id=user_id,
                task_id=task_id,
                tool_name=name,
                success=False,
                error=str(e)
            )
            return ToolResult(tool_name=name, success=False, result=None, error=str(e))

        # Check permission layer before execution
        if not tool.has_permission(user_role):
            error_msg = f"Role '{user_role}' is not authorized to execute tool '{name}'."
            logger.warning(error_msg)
            audit_logger.log_tool_execution(
                user_id=user_id,
                task_id=task_id,
                tool_name=name,
                success=False,
                error=error_msg
            )
            return ToolResult(tool_name=name, success=False, result=None, error=error_msg)

        # Execute the tool
        try:
            result = await tool.execute(user_role=user_role, **kwargs)
            # Standardize success status if result was missing error
            success = result.success
            error_msg = result.error
        except Exception as e:
            logger.exception(f"Tool {name} crashed during execution.")
            success = False
            error_msg = f"Internal execution error: {e}"
            result = ToolResult(tool_name=name, success=False, result=None, error=error_msg)

        # Audit log the execution
        audit_logger.log_tool_execution(
            user_id=user_id,
            task_id=task_id,
            tool_name=name,
            success=success,
            error=error_msg
        )

        return result


# Global Registry Instance
tool_registry = ToolRegistry()
