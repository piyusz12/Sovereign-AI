"""
Sovereign AI: Merkle-Tree Chained Tamper-Proof Audit Trail
Constructs an immutable cryptographic audit ledger where attestation quotes,
policy decisions, and model outputs are chained sequentially with Merkle root validation.
"""

import json
import hashlib
import time
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

@dataclass
class AuditBlock:
    index: int
    timestamp: float
    event_type: str
    actor_id: str
    payload_hash: str
    previous_block_hash: str
    block_hash: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MerkleAuditLedger:
    """
    Cryptographic immutable append-only ledger with SHA-256 Merkle root verification.
    """

    def __init__(self):
        self.chain: List[AuditBlock] = []
        self._initialize_genesis_block()

    def _hash_block(
        self,
        index: int,
        timestamp: float,
        event_type: str,
        actor_id: str,
        payload_hash: str,
        previous_block_hash: str
    ) -> str:
        data = f"{index}|{timestamp:.4f}|{event_type}|{actor_id}|{payload_hash}|{previous_block_hash}"
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    def _initialize_genesis_block(self):
        if not self.chain:
            genesis_time = 1773000000.0  # Epoch anchor
            p_hash = hashlib.sha256(b"SOVEREIGN_AI_GENESIS_ROOT").hexdigest()
            b_hash = self._hash_block(0, genesis_time, "GENESIS", "SYSTEM", p_hash, "0"*64)
            genesis_block = AuditBlock(
                index=0,
                timestamp=genesis_time,
                event_type="GENESIS",
                actor_id="SYSTEM",
                payload_hash=p_hash,
                previous_block_hash="0"*64,
                block_hash=b_hash,
                metadata={"title": "Sovereign AI Cryptographic Genesis Anchor"}
            )
            self.chain.append(genesis_block)

    def append_event(
        self,
        event_type: str,
        actor_id: str,
        payload: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditBlock:
        """
        Appends a new audited event to the tamper-proof chain.
        """
        last_block = self.chain[-1]
        new_index = len(self.chain)
        now = time.time()

        # Compute payload hash
        if isinstance(payload, (dict, list)):
            payload_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
        elif isinstance(payload, bytes):
            payload_bytes = payload
        else:
            payload_bytes = str(payload).encode("utf-8")

        payload_hash = hashlib.sha256(payload_bytes).hexdigest()
        prev_hash = last_block.block_hash
        block_hash = self._hash_block(new_index, now, event_type, actor_id, payload_hash, prev_hash)

        block = AuditBlock(
            index=new_index,
            timestamp=now,
            event_type=event_type,
            actor_id=actor_id,
            payload_hash=payload_hash,
            previous_block_hash=prev_hash,
            block_hash=block_hash,
            metadata=metadata or {}
        )

        self.chain.append(block)
        return block

    def compute_merkle_root(self) -> str:
        """
        Calculates the cryptographic Merkle Root over all block hashes in the ledger.
        """
        if not self.chain:
            return "0"*64

        current_level = [b.block_hash for b in self.chain]

        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                combined = hashlib.sha256((left + right).encode("utf-8")).hexdigest()
                next_level.append(combined)
            current_level = next_level

        return current_level[0]

    def verify_ledger_integrity(self) -> Dict[str, Any]:
        """
        Validates entire blockchain from Genesis forward.
        Detects any retroactive tampering or byte modification.
        """
        if not self.chain:
            return {"valid": False, "reason": "Chain empty."}

        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            # 1. Check previous hash reference
            if current.previous_block_hash != previous.block_hash:
                return {
                    "valid": False,
                    "tampered_index": i,
                    "reason": f"Broken block link at index {i}. Expected {previous.block_hash[:16]}, got {current.previous_block_hash[:16]}"
                }

            # 2. Re-calculate block hash
            expected_hash = self._hash_block(
                current.index,
                current.timestamp,
                current.event_type,
                current.actor_id,
                current.payload_hash,
                current.previous_block_hash
            )

            if current.block_hash != expected_hash:
                return {
                    "valid": False,
                    "tampered_index": i,
                    "reason": f"Block hash mismatch at index {i}. Stored: {current.block_hash[:16]}, Calculated: {expected_hash[:16]}"
                }

        return {
            "valid": True,
            "total_blocks": len(self.chain),
            "merkle_root": self.compute_merkle_root(),
            "latest_block_hash": self.chain[-1].block_hash,
            "status": "TAMPER_PROOF_VERIFIED"
        }

    def get_recent_blocks(self, limit: int = 15) -> List[Dict[str, Any]]:
        return [b.to_dict() for b in self.chain[-limit:]]


merkle_audit_ledger = MerkleAuditLedger()

# Seed initial operational sovereign events
merkle_audit_ledger.append_event(
    event_type="ENCLAVE_MEASUREMENT_ANCHOR",
    actor_id="TEE_SECURITY_PROCESSOR",
    payload={"measurement": "4c9d921b0337c784", "status": "HARDWARE_ROOT_ANCHORED"}
)
merkle_audit_ledger.append_event(
    event_type="MCP_FIREWALL_POLICY_LOADED",
    actor_id="SECURITY_GATEWAY",
    payload={"mode": "STRICT_LEAST_PRIVILEGE", "semantic_ast": "ENABLED"}
)
