from datetime import datetime, timezone
from pydantic import BaseModel, Field
from typing import Optional, List


class ConnectionEvent(BaseModel):
    pid: int = Field(..., description="Process ID")
    process_name: str = Field(..., description="Name of the process (e.g., python.exe, postgres.exe)")
    local_address: str = Field(..., description="Local IP and port")
    remote_address: Optional[str] = Field(None, description="Remote IP and port if applicable")
    status: str = Field(..., description="Connection status (e.g., ESTABLISHED, LISTEN)")
    classification: str = Field("UNKNOWN", description="LOCAL, PRIVATE, EXTERNAL, UNKNOWN")
    action: str = Field("ALLOW", description="ALLOW or BLOCK based on policy")
    bytes_sent: int = Field(0, description="Bytes sent (if retrievable)")
    bytes_recv: int = Field(0, description="Bytes received (if retrievable)")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Time of observation")


class NetworkPolicyDecision(BaseModel):
    ip_address: str
    classification: str
    decision: str
    reason: Optional[str] = None


class SovereigntyStatus(BaseModel):
    network_egress: str = Field("BLOCKED", description="Current network egress policy status")
    external_ai_apis: str = Field("DISABLED", description="Status of external AI APIs")
    external_connections: int = Field(0, description="Number of currently active external connections")
    blocked_attempts: int = Field(0, description="Total number of blocked external attempts")
    data_sent_externally_kb: float = Field(0.0, description="Data leaked/sent externally in KB")
    active_connections: List[ConnectionEvent] = Field(default_factory=list, description="Currently active connections")
    ai_components: dict[str, str] = Field(
        default_factory=lambda: {
            "Reasoning LLM": "LOCAL",
            "Vision Model": "LOCAL",
            "Embeddings": "LOCAL",
            "Reranker": "LOCAL",
            "Vector Database": "LOCAL"
        },
        description="Status of AI components"
    )
    is_sovereign: bool = Field(True, description="Overall sovereignty status flag")
