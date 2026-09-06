"""
Sovereign AI Workbench — Security Policy Engine (Phase 25)

Central decision-maker for all agent and user actions.
Evaluates Context (User + Action + Resource) -> ALLOW, DENY, or REQUIRE_APPROVAL.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger("sovereign.security.engine")

class Decision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"


@dataclass
class SecurityContext:
    user_role: str
    action: str
    resource: str = "*"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SecurityResult:
    decision: Decision
    reason: str


class SecurityPolicyEngine:
    def __init__(self):
        # List of rule evaluators: Callable[[SecurityContext], SecurityResult | None]
        self._rules: list[Callable[[SecurityContext], SecurityResult | None]] = []
        self._audit_events: list[dict] = []

    def register_rule(self, rule_evaluator: Callable[[SecurityContext], SecurityResult | None]):
        """Register a policy rule evaluator."""
        self._rules.append(rule_evaluator)

    def evaluate(self, context: SecurityContext) -> SecurityResult:
        """
        Evaluate a context against all registered rules.
        First explicit DENY or REQUIRE_APPROVAL wins.
        If any rule explicitly ALLOWS and no subsequent rule DENYs, it is ALLOWED.
        If no rules match, it defaults to DENY (fail-closed).
        """
        final_decision = None
        final_reason = "No matching rules found (default fail-closed)"

        for rule in self._rules:
            result = rule(context)
            if result:
                if result.decision == Decision.DENY:
                    self._record_audit(context, result)
                    return result  # Immediate deny
                elif result.decision == Decision.REQUIRE_APPROVAL:
                    final_decision = result.decision
                    final_reason = result.reason
                elif result.decision == Decision.ALLOW and final_decision is None:
                    final_decision = result.decision
                    final_reason = result.reason

        # Default to DENY if no explicit ALLOW or REQUIRE_APPROVAL was hit
        if final_decision is None:
            result = SecurityResult(Decision.DENY, final_reason)
            self._record_audit(context, result)
            return result
            
        result = SecurityResult(final_decision, final_reason)
        self._record_audit(context, result)
        return result
        
    def _record_audit(self, context: SecurityContext, result: SecurityResult):
        event = {
            "action": context.action,
            "user_role": context.user_role,
            "resource": context.resource,
            "decision": result.decision.value,
            "reason": result.reason,
            "metadata": context.metadata
        }
        self._audit_events.append(event)
        
        if result.decision == Decision.DENY:
            logger.warning("SECURITY DENY: [%s] %s on %s by %s. Reason: %s", 
                           context.action, context.resource, context.user_role, context.user_role, result.reason)
        elif result.decision == Decision.REQUIRE_APPROVAL:
            logger.info("SECURITY APPROVAL REQ: [%s] %s on %s by %s", 
                        context.action, context.resource, context.user_role, context.user_role)
        else:
            logger.debug("SECURITY ALLOW: [%s] %s on %s", context.action, context.resource, context.user_role)

    def get_audit_events(self) -> list[dict]:
        return self._audit_events

# Global Singleton
policy_engine = SecurityPolicyEngine()
