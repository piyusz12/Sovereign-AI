"""
Sovereign AI Workbench — Base Tool

Abstract base class for all agent tools.
Every tool has permission checking and audit logging.

Architecture:
    LLM → Tool request → Permission layer → Tool execution → Tool result → LLM
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional

logger = logging.getLogger("sovereign.tools")


@dataclass
class ToolPermission:
    """Permission configuration for a tool."""
    name: str
    allowed_roles: list[str]
    requires_approval: bool = False
    blocked: bool = False
    description: str = ""


@dataclass
class ToolResult:
    """Standardized result from tool execution."""
    tool_name: str
    success: bool
    result: Any
    error: Optional[str] = None
    duration_ms: float = 0.0
    metadata: dict = None  # type: ignore[assignment]

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseTool(ABC):
    """
    Abstract base class for all agent tools.

    Every tool:
    1. Checks permissions before execution
    2. Logs the action for audit
    3. Returns a standardized ToolResult
    4. Never accesses external networks
    """

    def __init__(self, name: str, description: str, permission: Optional[ToolPermission] = None):
        self.name = name
        self.description = description
        self.permission = permission or ToolPermission(
            name=name,
            allowed_roles=["admin", "engineering", "operations"],
            description=description,
        )

    async def execute(self, user_role: str = "engineering", **kwargs) -> ToolResult:
        """
        Execute the tool with permission checking and audit logging.
        """
        start = time.time()

        # Check permissions
        if not self.has_permission(user_role):
            return ToolResult(
                tool_name=self.name,
                success=False,
                result=None,
                error=f"Permission denied for role '{user_role}' on tool '{self.name}'",
                duration_ms=0.0,
            )

        if self.permission.blocked:
            return ToolResult(
                tool_name=self.name,
                success=False,
                result=None,
                error=f"Tool '{self.name}' is BLOCKED by security policy",
                duration_ms=0.0,
            )

        if self.permission.requires_approval:
            logger.warning("Tool '%s' requires approval — auto-approval for prototype", self.name)

        # Execute
        try:
            result = await self._run(**kwargs)
            duration = round((time.time() - start) * 1000, 2)
            logger.info("Tool '%s' completed in %.2f ms", self.name, duration)
            return ToolResult(
                tool_name=self.name,
                success=True,
                result=result,
                duration_ms=duration,
            )
        except Exception as e:
            duration = round((time.time() - start) * 1000, 2)
            logger.error("Tool '%s' failed: %s", self.name, e)
            return ToolResult(
                tool_name=self.name,
                success=False,
                result=None,
                error=str(e),
                duration_ms=duration,
            )

    @abstractmethod
    async def _run(self, **kwargs) -> Any:
        """Implement the actual tool logic. Override in subclasses."""
        ...

    def has_permission(self, user_role: str) -> bool:
        """Check if the user role has permission to use this tool."""
        return user_role in self.permission.allowed_roles

    def to_schema(self) -> dict:
        """Return tool schema for LLM function calling."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
            },
        }
