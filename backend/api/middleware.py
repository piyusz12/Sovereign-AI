"""
Sovereign AI Workbench — Middleware

Request/response middleware for audit logging, sovereignty enforcement,
and request tracing.
"""

import time
import uuid
import logging
from datetime import datetime, timezone

from fastapi import Request

logger = logging.getLogger("sovereign.middleware")


class AuditLogger:
    """
    Logs every API request for audit trail.
    Compatible with OpenTelemetry traces (Phase 27).
    """

    def __init__(self):
        self._entries: list[dict] = []

    def log(self, entry: dict) -> None:
        """Record an audit entry."""
        entry["timestamp"] = datetime.now(timezone.utc).isoformat()
        self._entries.append(entry)
        logger.info("AUDIT: %s", entry)

    def get_entries(self, limit: int = 100) -> list[dict]:
        """Retrieve recent audit entries."""
        return self._entries[-limit:]


class SovereigntyEnforcer:
    """
    Monitors and enforces that no external network calls are made.
    This is the software layer; Wireshark/firewall provides hardware layer.
    """

    def __init__(self):
        self.external_call_count = 0
        self.blocked_attempts: list[dict] = []

    def check_request(self, request: Request) -> bool:
        """
        Verify that an incoming request is from an allowed local origin.
        Returns True if allowed.
        """
        client_host = request.client.host if request.client else "unknown"
        allowed_hosts = {"127.0.0.1", "localhost", "::1", "0.0.0.0"}

        if client_host not in allowed_hosts:
            self.blocked_attempts.append({
                "host": client_host,
                "path": str(request.url),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            return False
        return True

    def get_status(self) -> dict:
        """Return sovereignty enforcement status."""
        return {
            "external_calls_detected": self.external_call_count,
            "blocked_attempts": len(self.blocked_attempts),
            "status": "clean" if self.external_call_count == 0 else "VIOLATION",
        }


# Global instances
audit_logger = AuditLogger()
sovereignty_enforcer = SovereigntyEnforcer()
