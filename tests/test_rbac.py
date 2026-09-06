"""
Tests — RBAC (Role-Based Access Control)

Verifies that documents are filtered BEFORE retrieval.
"""

import pytest
from backend.security.rbac import RBACEnforcer


@pytest.fixture
def rbac():
    return RBACEnforcer()


class TestRBAC:
    """Test role-based access control."""

    def test_admin_access_all(self, rbac):
        """Admin can access all departments."""
        assert rbac.can_access_document("admin", "finance") is True
        assert rbac.can_access_document("admin", "engineering") is True
        assert rbac.can_access_document("admin", "hr") is True

    def test_engineering_access_engineering(self, rbac):
        """Engineering can access engineering docs."""
        assert rbac.can_access_document("engineering", "engineering") is True
        assert rbac.can_access_document("engineering", "public") is True

    def test_engineering_cannot_access_finance(self, rbac):
        """Engineering CANNOT access finance docs."""
        assert rbac.can_access_document("engineering", "finance") is False

    def test_finance_cannot_access_engineering(self, rbac):
        """Finance CANNOT access engineering docs."""
        assert rbac.can_access_document("finance", "engineering") is False

    def test_finance_access_finance(self, rbac):
        """Finance can access finance docs."""
        assert rbac.can_access_document("finance", "finance") is True

    def test_operations_cross_access(self, rbac):
        """Operations can access operations AND engineering."""
        assert rbac.can_access_document("operations", "operations") is True
        assert rbac.can_access_document("operations", "engineering") is True

    def test_unknown_role_denied(self, rbac):
        """Unknown role is denied all access."""
        assert rbac.can_access_document("unknown_role", "engineering") is False

    def test_tool_permissions(self, rbac):
        """Finance cannot execute code."""
        assert rbac.has_permission("engineering", "agent.execute_code") is True
        assert rbac.has_permission("finance", "agent.execute_code") is False

    def test_qdrant_filter_admin(self, rbac):
        """Admin gets no filter (sees everything)."""
        f = rbac.get_qdrant_filter("admin")
        assert f == {}

    def test_qdrant_filter_engineering(self, rbac):
        """Engineering gets department filter."""
        f = rbac.get_qdrant_filter("engineering")
        assert "must" in f
