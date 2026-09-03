"""
Sovereign AI Workbench — Audit Logging

Structured audit logging for every agent operation.
Compatible with OpenTelemetry traces (Phase 27).
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("sovereign.security.audit")


class AuditLog:
    """
    Structured audit logger.

    Logs: user, model, tools, documents, results, timing.
    Stored locally for sovereignty compliance.
    """

    def __init__(self, log_dir: str = "./data/output/audit"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._entries: list[dict] = []

    def log_event(
        self,
        event_type: str,
        user: str = "system",
        task_id: Optional[str] = None,
        model: Optional[str] = None,
        tool: Optional[str] = None,
        documents: Optional[list[str]] = None,
        result: str = "success",
        duration_ms: float = 0.0,
        details: Optional[dict] = None,
    ) -> dict:
        """Log an audit event."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "user": user,
            "task_id": task_id,
            "model": model,
            "tool": tool,
            "documents": documents or [],
            "result": result,
            "duration_ms": duration_ms,
            "details": details or {},
        }

        self._entries.append(entry)
        logger.info("AUDIT [%s]: %s → %s", event_type, user, result)
        return entry

    def get_entries(self, limit: int = 100, event_type: Optional[str] = None) -> list[dict]:
        """Get recent audit entries, optionally filtered by type."""
        entries = self._entries
        if event_type:
            entries = [e for e in entries if e["event_type"] == event_type]
        return entries[-limit:]

    def save_to_file(self) -> str:
        """Persist audit log to disk."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filepath = self.log_dir / f"audit_{timestamp}.jsonl"

        with open(filepath, "w", encoding="utf-8") as f:
            for entry in self._entries:
                f.write(json.dumps(entry) + "\n")

        logger.info("Audit log saved: %s (%d entries)", filepath, len(self._entries))
        return str(filepath)


# Global instance
audit_log = AuditLog()
