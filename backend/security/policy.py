"""
Sovereign AI Workbench — Agentic Action Firewall

Policy engine that controls what the AI agent is allowed to do.
BLOCKED actions are never executed, regardless of the agent's request.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("sovereign.security.policy")


class ActionDecision(str, Enum):
    ALLOWED = "allowed"
    APPROVAL_REQUIRED = "approval_required"
    BLOCKED = "blocked"


@dataclass
class PolicyRule:
    """A single policy rule."""
    action: str
    decision: ActionDecision
    reason: str


# Default policy — these actions are NEVER allowed
DEFAULT_POLICY: dict[str, PolicyRule] = {
    "read_file": PolicyRule("read_file", ActionDecision.ALLOWED, "Reading files is safe"),
    "write_file": PolicyRule("write_file", ActionDecision.ALLOWED, "Writing to output directory"),
    "list_files": PolicyRule("list_files", ActionDecision.ALLOWED, "Listing files is safe"),
    "search_documents": PolicyRule("search_documents", ActionDecision.ALLOWED, "Internal search"),
    "calculate": PolicyRule("calculate", ActionDecision.ALLOWED, "Math is safe"),
    "run_python": PolicyRule("run_python", ActionDecision.ALLOWED, "Sandboxed execution"),
    "create_docx": PolicyRule("create_docx", ActionDecision.ALLOWED, "Document generation"),
    "create_xlsx": PolicyRule("create_xlsx", ActionDecision.ALLOWED, "Spreadsheet generation"),
    "create_pptx": PolicyRule("create_pptx", ActionDecision.ALLOWED, "Presentation generation"),
    "inspect_image": PolicyRule("inspect_image", ActionDecision.ALLOWED, "Local vision analysis"),
    # BLOCKED ACTIONS — sovereignty enforcement
    "send_external": PolicyRule("send_external", ActionDecision.BLOCKED, "SOVEREIGNTY VIOLATION — no external network"),
    "network_request": PolicyRule("network_request", ActionDecision.BLOCKED, "SOVEREIGNTY VIOLATION — no external network"),
    "delete_file": PolicyRule("delete_file", ActionDecision.APPROVAL_REQUIRED, "Destructive action"),
    "modify_config": PolicyRule("modify_config", ActionDecision.APPROVAL_REQUIRED, "System configuration"),
    "install_package": PolicyRule("install_package", ActionDecision.BLOCKED, "No runtime installs"),
}


class ActionFirewall:
    """
    Agentic Action Firewall.
    Every agent action passes through this firewall before execution.
    """

    def __init__(self, policy: dict[str, PolicyRule] | None = None):
        self.policy = policy or dict(DEFAULT_POLICY)
        self._blocked_attempts: list[dict] = []

    def check(self, action: str, user_role: str = "engineering") -> PolicyRule:
        """
        Check if an action is allowed by policy.

        Returns the PolicyRule for the action.
        """
        rule = self.policy.get(action)

        if rule is None:
            # Unknown action — block by default (fail-closed)
            rule = PolicyRule(action, ActionDecision.BLOCKED, "Unknown action — blocked by default")

        if rule.decision == ActionDecision.BLOCKED:
            self._blocked_attempts.append({
                "action": action,
                "user_role": user_role,
                "reason": rule.reason,
            })
            logger.warning("BLOCKED action '%s' by user '%s': %s", action, user_role, rule.reason)

        return rule

    def get_blocked_attempts(self) -> list[dict]:
        """Return history of blocked action attempts."""
        return self._blocked_attempts


# Global instance
action_firewall = ActionFirewall()
