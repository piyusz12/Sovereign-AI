"""
Sovereign AI Workbench — RBAC (Role-Based Access Control)

Enforces document access control BEFORE retrieval, not after.
The LLM should never see restricted documents — they are filtered
at the vector search level.

Also enforces workflow-level access control: each role is only
allowed to execute specific workflows.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger("sovereign.security.rbac")


@dataclass
class RolePermission:
    """Permissions for a role."""
    role: str
    departments: list[str]  # Accessible departments
    document_types: list[str]  # Accessible document types
    permissions: list[str]  # Explicit string permissions
    workflow_access: list[str] = field(default_factory=list)  # Allowed workflow names


# Role definitions
ROLE_PERMISSIONS: dict[str, RolePermission] = {
    "admin": RolePermission(
        role="admin",
        departments=["all"],
        document_types=["all"],
        permissions=["all"],
        workflow_access=["all"],  # Full access to every workflow
    ),
    "engineering": RolePermission(
        role="engineering",
        departments=["engineering", "operations", "public"],
        document_types=["inspection_report", "sop", "pid", "specification", "manual"],
        permissions=["ai.chat", "agent.execute_code", "agent.run", "document.read", "document.upload", "rag.search", "report.create", "model.load", "model.unload", "model.manage"],
        workflow_access=["coding", "assistance"],  # Coding + reasoning only
    ),
    "finance": RolePermission(
        role="finance",
        departments=["finance", "procurement", "public"],
        document_types=["budget", "invoice", "purchase_order", "financial_report"],
        permissions=["ai.chat", "ai.vision", "document.read", "rag.search", "report.create"],
        workflow_access=["inspection", "pid_vision", "assistance"],  # Everything except coding
    ),
    "procurement": RolePermission(
        role="procurement",
        departments=["procurement", "finance", "public"],
        document_types=["purchase_order", "vendor_report", "contract", "invoice"],
        permissions=["ai.chat", "document.read", "document.upload", "rag.search", "report.create"],
        workflow_access=["inspection", "assistance"],
    ),
    "hr": RolePermission(
        role="hr",
        departments=["hr", "public"],
        document_types=["policy", "compliance", "training"],
        permissions=["ai.chat", "document.read", "rag.search"],
        workflow_access=["assistance"],
    ),
    "operations": RolePermission(
        role="operations",
        departments=["operations", "engineering", "public"],
        document_types=["inspection_report", "sop", "maintenance_log", "telemetry"],
        permissions=["ai.chat", "ai.vision", "document.read", "document.upload", "rag.search", "agent.execute_code", "report.create"],
        workflow_access=["inspection", "pid_vision", "assistance"],
    ),
}


class RBACEnforcer:
    """
    Enforce role-based access control.

    CRITICAL: Filtering happens BEFORE retrieval.
    The vector search query includes role-based filters so that
    restricted documents are never returned to the LLM.

    UNSAFE approach (DO NOT USE):
        vector search EVERYTHING → LLM hides restricted results

    SAFE approach (THIS IMPLEMENTATION):
        RBAC filter → vector search only allowed documents → LLM sees only permitted data
    """

    def get_permission(self, role: str) -> Optional[RolePermission]:
        """Get permissions for a role."""
        return ROLE_PERMISSIONS.get(role)

    def can_access_document(self, role: str, document_dept: str, document_type: str = "") -> bool:
        """Check if a role can access a specific document."""
        perm = self.get_permission(role)
        if not perm:
            return False
        if "all" in perm.departments:
            return True
        if document_dept not in perm.departments:
            return False
        if document_type and "all" not in perm.document_types:
            if document_type not in perm.document_types:
                return False
        return True

    def get_qdrant_filter(self, role: str) -> dict:
        """
        Build a Qdrant filter that restricts search to allowed documents.
        This filter is applied BEFORE retrieval.
        """
        perm = self.get_permission(role)
        if not perm or "all" in perm.departments:
            return {}  # Admin — no filter

        return {
            "must": [
                {
                    "key": "department",
                    "match": {"any": perm.departments},
                }
            ]
        }

    def has_permission(self, role: str, permission: str) -> bool:
        """Check if a role has a specific string permission."""
        perm = self.get_permission(role)
        if not perm:
            return False
        if "all" in perm.permissions:
            return True
        return permission in perm.permissions

    def can_access_workflow(self, role: str, workflow_name: str) -> bool:
        """Check if a role is allowed to execute a specific workflow."""
        perm = self.get_permission(role)
        if not perm:
            return False
        if "all" in perm.workflow_access:
            return True
        return workflow_name in perm.workflow_access

    def get_accessible_workflows(self, role: str) -> list[str]:
        """Return list of workflow names accessible to this role."""
        perm = self.get_permission(role)
        if not perm:
            return []
        if "all" in perm.workflow_access:
            return ["inspection", "coding", "pid_vision", "assistance"]
        return list(perm.workflow_access)

    def can_manage_models(self, role: str) -> bool:
        """Check if a role is allowed to load or unload models."""
        perm = self.get_permission(role)
        if not perm:
            return False
        if "all" in perm.permissions or "model.manage" in perm.permissions or "model.load" in perm.permissions:
            return True
        return role in ("admin", "engineering")


# Global instance
rbac_enforcer = RBACEnforcer()
