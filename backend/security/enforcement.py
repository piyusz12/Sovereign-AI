"""
Sovereign AI Workbench — Security Enforcement (Phase 25)

Wiring up the SecurityPolicyEngine with default rules and
providing decorators/utilities for tool authorization.
"""

from backend.security.engine import policy_engine, SecurityContext, Decision
from backend.security.rules import get_default_rules
import logging

logger = logging.getLogger("sovereign.security.enforcement")

# Register default rules
for rule in get_default_rules():
    policy_engine.register_rule(rule)


class SecurityException(Exception):
    pass


def authorize_action(user_role: str, action: str, resource: str = "*", metadata: dict = None) -> None:
    """
    Authorizes an action. Raises SecurityException if DENY or REQUIRE_APPROVAL.
    (REQUIRE_APPROVAL would typically trigger an async workflow, but for sync enforcement we raise)
    """
    context = SecurityContext(
        user_role=user_role,
        action=action,
        resource=resource,
        metadata=metadata or {}
    )
    result = policy_engine.evaluate(context)
    
    if result.decision == Decision.DENY:
        raise SecurityException(f"Action '{action}' on '{resource}' DENIED: {result.reason}")
    if result.decision == Decision.REQUIRE_APPROVAL:
        raise SecurityException(f"Action '{action}' on '{resource}' REQUIRES APPROVAL: {result.reason}")
        
    return True
