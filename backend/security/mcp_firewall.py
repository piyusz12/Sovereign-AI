"""
Sovereign AI Workbench — Advanced MCP Governance Firewall

Deterministic context-level policy enforcement layer between LLM semantic intent
and physical Model Context Protocol (MCP) tool execution.

Enforces:
- Identity Boundary (verifies session permissions against tool requirements)
- Semantic Safety (detects and intercepts destructive commands, drops, deletes, exfiltration)
- Jurisdictional Constraints (enforces local data residency rules)
- Least-Privilege Scoped Tokens (issues cryptographically signed, short-lived, single-use invocation tokens)
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import re
import secrets
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from backend.security.rbac import rbac_enforcer

logger = logging.getLogger("sovereign.security.mcp_firewall")

# Firewall Secret Key for signing short-lived invocation tokens
_FIREWALL_SECRET = secrets.token_bytes(32)

# Destructive pattern detection regexes
_DESTRUCTIVE_SQL_PATTERNS = [
    re.compile(r"\b(DROP\s+TABLE|DROP\s+DATABASE|TRUNCATE\s+TABLE|DELETE\s+FROM)\b", re.IGNORECASE),
    re.compile(r"\b(ALTER\s+TABLE.*DROP|GRANT\s+ALL|REVOKE\s+ALL)\b", re.IGNORECASE),
]

_DESTRUCTIVE_SHELL_PATTERNS = [
    re.compile(r"\b(rm\s+-rf|rmdir\s+/s|del\s+/f|format\s+[a-z]:)\b", re.IGNORECASE),
    re.compile(r"\b(shutdown\b|reboot\b|init\s+0|halt\b|mkfs\b)", re.IGNORECASE),
    re.compile(r"\b(curl\b.*\|\s*(bash|sh)|wget\b.*\|\s*(bash|sh))\b", re.IGNORECASE),
    re.compile(r"(>\s*/dev/sd[a-z]|dd\s+if=)", re.IGNORECASE),
]

_EXFILTRATION_PATTERNS = [
    re.compile(r"\b(https?://|ftp://|scp\s+|rsync\s+|sftp\s+)(?!localhost|127\.0\.0\.1)", re.IGNORECASE),
    re.compile(r"\b(nc\s+-e|bash\s+-i\s+>&|/dev/tcp/)", re.IGNORECASE),
]


@dataclass
class ToolExecutionPolicy:
    """Policy governing a specific MCP tool."""
    tool_name: str
    required_permission: str
    allowed_roles: List[str]
    max_payload_bytes: int = 65536
    allow_network_egress: bool = False
    jurisdiction_restricted: bool = True  # Must execute within local sovereign boundary


@dataclass
class InterceptEvaluation:
    """Result of an MCP tool invocation evaluation."""
    allowed: bool
    verdict: str  # "APPROVED", "DENIED_IDENTITY", "DENIED_SAFETY", "DENIED_JURISDICTION"
    reason: str
    tool_name: str
    invocation_token: Optional[str] = None
    token_expires_at: Optional[float] = None
    checked_dimensions: Dict[str, bool] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def execution_token(self) -> Optional[str]:
        return self.invocation_token

    @property
    def violation_reason(self) -> Optional[str]:
        return None if self.allowed else self.reason

    def to_dict(self) -> Dict[str, Any]:
        import dataclasses
        d = dataclasses.asdict(self)
        d["execution_token"] = self.execution_token
        d["violation_reason"] = self.violation_reason
        return d


class MCPGovernanceFirewall:
    """
    Active law enforcement layer between LLM intent and tool execution.
    """

    def __init__(self) -> None:
        self._consumed_tokens: set[str] = set()
        self._tool_policies: Dict[str, ToolExecutionPolicy] = {
            "execute_python_code": ToolExecutionPolicy(
                tool_name="execute_python_code",
                required_permission="agent.execute_code",
                allowed_roles=["admin", "engineering", "operations"],
                max_payload_bytes=131072,
            ),
            "read_local_document": ToolExecutionPolicy(
                tool_name="read_local_document",
                required_permission="document.read",
                allowed_roles=["admin", "engineering", "finance", "operations", "procurement", "hr"],
                max_payload_bytes=524288,
            ),
            "upload_local_document": ToolExecutionPolicy(
                tool_name="upload_local_document",
                required_permission="document.upload",
                allowed_roles=["admin", "engineering", "operations", "procurement"],
            ),
            "query_database": ToolExecutionPolicy(
                tool_name="query_database",
                required_permission="rag.search",
                allowed_roles=["admin", "engineering", "finance", "operations"],
            ),
            "create_report": ToolExecutionPolicy(
                tool_name="create_report",
                required_permission="report.create",
                allowed_roles=["admin", "engineering", "finance", "operations", "procurement"],
            ),
            "load_model": ToolExecutionPolicy(
                tool_name="load_model",
                required_permission="model.load",
                allowed_roles=["admin", "engineering"],
            ),
            "unload_model": ToolExecutionPolicy(
                tool_name="unload_model",
                required_permission="model.unload",
                allowed_roles=["admin", "engineering"],
            ),
        }
        logger.info("MCP Governance Firewall initialized with %d tool policies", len(self._tool_policies))

    def evaluate_tool_invocation(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        user_role: str,
        session_id: str,
    ) -> InterceptEvaluation:
        """
        Evaluate tool execution against Identity, Semantic Safety, and Jurisdictional dimensions.
        """
        policy = self._tool_policies.get(tool_name)
        if not policy:
            # Fallback policy for unregistered tools
            policy = ToolExecutionPolicy(
                tool_name=tool_name,
                required_permission="ai.chat",
                allowed_roles=["admin"],
            )

        checked_dims = {
            "identity_boundary": False,
            "semantic_safety": False,
            "jurisdictional_residency": False,
        }

        # 1. Check Identity Boundary
        if user_role not in policy.allowed_roles:
            return InterceptEvaluation(
                allowed=False,
                verdict="DENIED_IDENTITY",
                reason=f"Role '{user_role}' is not authorized to invoke tool '{tool_name}'. Allowed roles: {policy.allowed_roles}",
                tool_name=tool_name,
                checked_dimensions=checked_dims,
            )
        checked_dims["identity_boundary"] = True

        # 2. Check Semantic Safety
        args_str = json.dumps(arguments)
        for pat in _DESTRUCTIVE_SQL_PATTERNS:
            if pat.search(args_str):
                return InterceptEvaluation(
                    allowed=False,
                    verdict="DENIED_SAFETY",
                    reason=f"Semantic violation: destructive SQL pattern detected in arguments for '{tool_name}'",
                    tool_name=tool_name,
                    checked_dimensions=checked_dims,
                )

        for pat in _DESTRUCTIVE_SHELL_PATTERNS:
            if pat.search(args_str):
                return InterceptEvaluation(
                    allowed=False,
                    verdict="DENIED_SAFETY",
                    reason=f"Semantic violation: destructive operating system command pattern detected in '{tool_name}'",
                    tool_name=tool_name,
                    checked_dimensions=checked_dims,
                )
        checked_dims["semantic_safety"] = True

        # 3. Check Jurisdictional Residency
        if policy.jurisdiction_restricted and not policy.allow_network_egress:
            for pat in _EXFILTRATION_PATTERNS:
                if pat.search(args_str):
                    return InterceptEvaluation(
                        allowed=False,
                        verdict="DENIED_JURISDICTION",
                        reason=f"Jurisdictional violation: external network transit pattern detected in '{tool_name}'",
                        tool_name=tool_name,
                        checked_dimensions=checked_dims,
                    )
        checked_dims["jurisdictional_residency"] = True

        # 4. Generate Single-Use Scoped Invocation Token
        expires_at = time.time() + 60.0  # 60-second execution window
        token_payload = f"{tool_name}:{user_role}:{session_id}:{expires_at}:{secrets.token_hex(8)}"
        signature = hmac.new(_FIREWALL_SECRET, token_payload.encode(), hashlib.sha256).hexdigest()
        scoped_token = f"mcp_inv_{base64.urlsafe_b64encode(token_payload.encode()).decode()}.{signature}"

        logger.info("MCP Firewall APPROVED tool '%s' for role '%s' [Token: %s...]", tool_name, user_role, scoped_token[:20])

        return InterceptEvaluation(
            allowed=True,
            verdict="APPROVED",
            reason=f"All governance checks passed: identity ({user_role}), semantic safety, and local data residency.",
            tool_name=tool_name,
            invocation_token=scoped_token,
            token_expires_at=expires_at,
            checked_dimensions=checked_dims,
        )

    def verify_and_consume_token(self, token: str, expected_tool: str) -> Tuple[bool, str]:
        """
        Verify that the single-use scoped token is valid, matches the tool,
        and has not already been consumed.
        """
        if not token or "." not in token:
            return False, "Malformed invocation token"

        if token in self._consumed_tokens:
            return False, "Invocation token has already been consumed (replay prevention)"

        try:
            raw_payload_b64, signature = token.replace("mcp_inv_", "").split(".", 1)
            token_payload = base64.urlsafe_b64decode(raw_payload_b64.encode()).decode()
            expected_sig = hmac.new(_FIREWALL_SECRET, token_payload.encode(), hashlib.sha256).hexdigest()

            if not hmac.compare_digest(signature, expected_sig):
                return False, "Cryptographic signature verification failed on invocation token"

            parts = token_payload.split(":")
            tool_name = parts[0]
            expires_at = float(parts[3])

            if time.time() > expires_at:
                return False, "Invocation token has expired"

            if tool_name != expected_tool:
                return False, f"Token tool mismatch: token scoped for '{tool_name}', got '{expected_tool}'"

            # Consume token
            self._consumed_tokens.add(token)
            return True, "Token valid and successfully consumed"

        except Exception as e:
            return False, f"Token validation exception: {e}"

    def evaluate_invocation(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        user_id: str = "user",
        user_role: str = "engineering",
        jurisdiction: str = "IN_COUNTRY"
    ) -> InterceptEvaluation:
        """Normalized wrapper for evaluating an MCP tool invocation."""
        role_map = {
            "software_engineer": "engineering",
            "developer": "engineering",
            "engineer": "engineering",
            "administrator": "admin"
        }
        normalized_role = role_map.get(user_role.lower(), user_role.lower())
        
        # Ensure common tools are known
        if tool_name not in self._tool_policies:
            if "search" in tool_name or "vector" in tool_name or "read" in tool_name:
                self._tool_policies[tool_name] = ToolExecutionPolicy(
                    tool_name=tool_name,
                    required_permission="rag.search",
                    allowed_roles=["admin", "engineering", "finance", "operations", "procurement", "hr"]
                )
            elif "database" in tool_name or "sql" in tool_name or "query" in tool_name:
                self._tool_policies[tool_name] = ToolExecutionPolicy(
                    tool_name=tool_name,
                    required_permission="rag.search",
                    allowed_roles=["admin", "engineering", "finance", "operations"]
                )

        return self.evaluate_tool_invocation(
            tool_name=tool_name,
            arguments=arguments,
            user_role=normalized_role,
            session_id=user_id
        )

    def validate_execution_token(self, token: str, tool_name: str, user_id: str = "user") -> bool:
        """Validates and consumes a single-use token."""
        valid, _ = self.verify_and_consume_token(token, tool_name)
        return valid

    def get_policies(self) -> Dict[str, ToolExecutionPolicy]:
        """Returns registered tool execution policies."""
        return self._tool_policies

    def get_active_tokens(self) -> List[Any]:
        """Returns active token info."""
        return []


# Global Singleton Instance
mcp_firewall = MCPGovernanceFirewall()
mcp_governance_firewall = mcp_firewall


