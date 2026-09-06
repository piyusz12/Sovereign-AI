import logging
from dataclasses import dataclass
from typing import Dict, Literal
from backend.optimization.hardware import current_hardware

logger = logging.getLogger(__name__)

VRAMStatus = Literal["GREEN", "YELLOW", "RED"]

@dataclass
class VRAMState:
    total_mb: int
    used_mb: int
    free_mb: int
    status: VRAMStatus
    allocations: Dict[str, int] # model_id -> mb

class VRAMManager:
    def __init__(self):
        self.total_vram = current_hardware.gpu_vram_mb
        # Thresholds tailored for RTX 4060 (8192 MB)
        self.yellow_threshold = int(self.total_vram * 0.75) # ~6GB
        self.red_threshold = int(self.total_vram * 0.90)    # ~7.3GB
        
        self.allocations: Dict[str, int] = {}
        # Fixed overhead for CUDA context / OS display
        self.base_overhead_mb = 600 

    def get_state(self) -> VRAMState:
        used = self.base_overhead_mb + sum(self.allocations.values())
        free = self.total_vram - used
        
        status: VRAMStatus = "GREEN"
        if used > self.red_threshold:
            status = "RED"
        elif used > self.yellow_threshold:
            status = "YELLOW"
            
        return VRAMState(
            total_mb=self.total_vram,
            used_mb=used,
            free_mb=free,
            status=status,
            allocations=self.allocations.copy()
        )

    def can_allocate(self, required_mb: int) -> bool:
        """Check if allocating required_mb will keep us out of the RED zone (or at least within total limits)."""
        state = self.get_state()
        return (state.used_mb + required_mb) <= self.total_vram

    def allocate(self, owner_id: str, required_mb: int) -> bool:
        """Registers a VRAM allocation."""
        if not self.can_allocate(required_mb):
            logger.warning(f"VRAM allocation denied for {owner_id}: Need {required_mb}MB, Free {self.get_state().free_mb}MB")
            return False
        self.allocations[owner_id] = required_mb
        logger.debug(f"Allocated {required_mb}MB for {owner_id}")
        return True

    def release(self, owner_id: str):
        """Releases a VRAM allocation."""
        if owner_id in self.allocations:
            released = self.allocations.pop(owner_id)
            logger.debug(f"Released {released}MB from {owner_id}")

# Global VRAM Manager
vram_manager = VRAMManager()
