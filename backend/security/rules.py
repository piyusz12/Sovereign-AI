"""
Sovereign AI Workbench — Security Policy Rules (Phase 25)

Defines the individual rules that power the SecurityPolicyEngine.
"""

from backend.security.engine import SecurityContext, SecurityResult, Decision


def rule_allow_safe_reads(context: SecurityContext) -> SecurityResult | None:
    """Allow safe read operations."""
    safe_actions = ["read_file", "list_files", "search_documents", "calculate"]
    if context.action in safe_actions:
        return SecurityResult(Decision.ALLOW, "Read-only operation allowed")
    return None


def rule_enforce_sandbox_isolation(context: SecurityContext) -> SecurityResult | None:
    """Ensure sandbox execution has network disabled."""
    if context.action == "sandbox.execute":
        network_enabled = context.metadata.get("network_enabled", False)
        if network_enabled:
            return SecurityResult(Decision.DENY, "Sandbox network access is strictly prohibited.")
        return SecurityResult(Decision.ALLOW, "Sandbox execution meets isolation requirements.")
    return None


def rule_block_external_network(context: SecurityContext) -> SecurityResult | None:
    """Sovereignty check: block all external network requests by the agent."""
    if context.action in ["network_request", "send_external"]:
        return SecurityResult(Decision.DENY, "SOVEREIGNTY VIOLATION — External network requests blocked.")
    return None


def rule_require_approval_destructive(context: SecurityContext) -> SecurityResult | None:
    """Destructive actions require explicit approval."""
    if context.action in ["delete_file", "modify_config", "install_package"]:
        return SecurityResult(Decision.REQUIRE_APPROVAL, "Destructive/modification action requires human approval.")
    return None


def rule_rag_clearance(context: SecurityContext) -> SecurityResult | None:
    """Check if the user has clearance for the specified RAG namespace/document."""
    if context.action == "rag.search":
        # Example naive check: role must match namespace, or role is admin
        namespace = context.metadata.get("namespace", "general")
        if context.user_role == "admin":
            return SecurityResult(Decision.ALLOW, "Admin has access to all namespaces.")
        
        if namespace != "general" and context.user_role != namespace:
            return SecurityResult(Decision.DENY, f"Role '{context.user_role}' cannot access namespace '{namespace}'.")
            
        return SecurityResult(Decision.ALLOW, f"Access to namespace '{namespace}' granted.")
    return None


def get_default_rules() -> list:
    """Return the ordered list of default rules."""
    return [
        rule_block_external_network,
        rule_enforce_sandbox_isolation,
        rule_require_approval_destructive,
        rule_rag_clearance,
        rule_allow_safe_reads,
    ]
