from backend.sovereignty.schemas import NetworkPolicyDecision

def evaluate_network_policy(ip_address: str, classification: str) -> NetworkPolicyDecision:
    """
    Evaluates the network policy based on the IP classification.
    Returns ALLOW for local/private, BLOCK for external.
    """
    decision = "ALLOW"
    reason = None

    if classification == "EXTERNAL":
        decision = "BLOCK"
        reason = "External network access is prohibited by air-gapped policy."
    elif classification == "UNKNOWN":
        decision = "BLOCK"
        reason = "Unclassified IP addresses are blocked by default."
    else:
        # LOCAL or PRIVATE
        decision = "ALLOW"
        reason = "Internal network communication is permitted."

    return NetworkPolicyDecision(
        ip_address=ip_address,
        classification=classification,
        decision=decision,
        reason=reason
    )
