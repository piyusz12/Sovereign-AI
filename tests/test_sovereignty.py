import pytest
from backend.sovereignty.classifier import classify_destination
from backend.sovereignty.policy import evaluate_network_policy

def test_classifier():
    # Local
    assert classify_destination("127.0.0.1") == "LOCAL"
    assert classify_destination("::1") == "LOCAL"
    assert classify_destination("localhost") == "LOCAL"

    # Private
    assert classify_destination("192.168.1.100") == "PRIVATE"
    assert classify_destination("10.0.0.5") == "PRIVATE"
    assert classify_destination("172.16.0.1") == "PRIVATE"

    # External
    assert classify_destination("8.8.8.8") == "EXTERNAL"
    assert classify_destination("1.1.1.1") == "EXTERNAL"
    assert classify_destination("142.250.190.46") == "EXTERNAL"

    # Edge cases
    assert classify_destination("") == "LOCAL"
    assert classify_destination("invalid_ip") == "UNKNOWN"

def test_policy_allow_local():
    decision = evaluate_network_policy("127.0.0.1", "LOCAL")
    assert decision.decision == "ALLOW"
    assert decision.classification == "LOCAL"

def test_policy_allow_private():
    decision = evaluate_network_policy("192.168.1.1", "PRIVATE")
    assert decision.decision == "ALLOW"
    assert decision.classification == "PRIVATE"

def test_policy_block_external():
    decision = evaluate_network_policy("8.8.8.8", "EXTERNAL")
    assert decision.decision == "BLOCK"
    assert decision.classification == "EXTERNAL"
    assert "prohibited" in decision.reason

def test_policy_block_unknown():
    decision = evaluate_network_policy("invalid", "UNKNOWN")
    assert decision.decision == "BLOCK"
    assert decision.classification == "UNKNOWN"
