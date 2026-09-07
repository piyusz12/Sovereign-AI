"""
Sovereign AI Workbench — Security Audit Bridge

Provides backward-compatible and centralized security audit logging,
bridging security components and agent tools to the unified AuditService.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from backend.audit.service import audit_service

logger = logging.getLogger("sovereign.security.audit")


class SecurityAuditLogger:
    """Audit logger for security events and tool executions."""

    def log_event(
        self,
        event_type: str,
        user: Optional[str] = None,
        result: str = "ALLOWED",
        details: Optional[Dict[str, Any]] = None,
        resource: Optional[str] = None,
        action: Optional[str] = None,
    ) -> None:
        """Log a generic security event."""
        action_name = action or event_type
        status = "success" if result in ("ALLOWED", "SUCCESS") else "denied"
        decision = result
        try:
            audit_service.log(
                action=action_name,
                status=status,
                user_id=user,
                role=user,
                decision=decision,
                resource_id=resource,
                metadata=details or {},
            )
        except Exception as e:
            logger.warning("Failed to record security audit log: %s", e)

    def log_tool_execution(
        self,
        user_id: Optional[str],
        task_id: Optional[str],
        tool_name: str,
        success: bool,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log a tool execution event."""
        status = "success" if success else "failure"
        meta = metadata or {}
        if error:
            meta["error"] = str(error)
        if task_id:
            meta["task_id"] = str(task_id)

        try:
            audit_service.log(
                action="tool.execute",
                status=status,
                user_id=user_id,
                tool=tool_name,
                error_code="TOOL_ERROR" if not success else None,
                metadata=meta,
            )
        except Exception as e:
            logger.warning("Failed to record tool audit log: %s", e)


audit_logger = SecurityAuditLogger()
audit_log = audit_logger
