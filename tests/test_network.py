"""
Tests — Network Security / Sovereignty

Verifies that external network access is blocked.
"""

import pytest
from backend.security.policy import ActionFirewall, ActionDecision
from monitoring.sovereignty import SovereigntyMonitor


class TestActionFirewall:
    """Test the agentic action firewall."""

    def test_local_actions_allowed(self):
        """Local safe actions are allowed."""
        fw = ActionFirewall()
        assert fw.check("read_file").decision == ActionDecision.ALLOWED
        assert fw.check("search_documents").decision == ActionDecision.ALLOWED
        assert fw.check("calculate").decision == ActionDecision.ALLOWED
        assert fw.check("run_python").decision == ActionDecision.ALLOWED

    def test_external_network_blocked(self):
        """External network access is BLOCKED."""
        fw = ActionFirewall()
        assert fw.check("send_external").decision == ActionDecision.BLOCKED
        assert fw.check("network_request").decision == ActionDecision.BLOCKED

    def test_delete_requires_approval(self):
        """Destructive actions require approval."""
        fw = ActionFirewall()
        assert fw.check("delete_file").decision == ActionDecision.APPROVAL_REQUIRED

    def test_unknown_action_blocked(self):
        """Unknown actions are blocked by default (fail-closed)."""
        fw = ActionFirewall()
        result = fw.check("completely_unknown_action")
        assert result.decision == ActionDecision.BLOCKED

    def test_blocked_attempts_logged(self):
        """Blocked attempts are recorded."""
        fw = ActionFirewall()
        fw.check("send_external")
        fw.check("network_request")
        attempts = fw.get_blocked_attempts()
        assert len(attempts) == 2


class TestSovereigntyMonitor:
    """Test sovereignty network monitor."""

    def test_local_connection_allowed(self):
        """Local connections are tracked and allowed."""
        monitor = SovereigntyMonitor()
        result = monitor.record_connection_attempt("127.0.0.1", 8080)
        assert result is True
        assert monitor.external_requests == 0

    def test_external_connection_detected(self):
        """External connections are detected as violations."""
        monitor = SovereigntyMonitor()
        result = monitor.record_connection_attempt("8.8.8.8", 443)
        assert result is False
        assert monitor.external_requests == 1

    def test_dashboard_clean(self):
        """Dashboard shows clean status when no violations."""
        monitor = SovereigntyMonitor()
        monitor.record_local_call("/health")
        data = monitor.get_dashboard_data()
        assert data["sovereign"] is True
        assert data["status"] == "CLEAN"

    def test_dashboard_violation(self):
        """Dashboard shows violation when external call detected."""
        monitor = SovereigntyMonitor()
        monitor.record_connection_attempt("api.openai.com", 443)
        data = monitor.get_dashboard_data()
        assert data["sovereign"] is False
        assert data["status"] == "VIOLATION_DETECTED"
