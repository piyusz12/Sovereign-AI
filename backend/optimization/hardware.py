import platform
import logging
from dataclasses import dataclass
import psutil

logger = logging.getLogger(__name__)

@dataclass
class HardwareProfile:
    name: str
    gpu_vram_mb: int
    system_ram_mb: int
    cpu_cores: int

def detect_hardware() -> HardwareProfile:
    """
    Detects hardware. Falls back to RTX 4060 profile if detection fails.
    """
    # Fallback/Default for SIH Demo
    profile = HardwareProfile(
        name="rtx4060_8gb",
        gpu_vram_mb=8192,
        system_ram_mb=16384,
        cpu_cores=8
    )

    try:
        # Detect RAM
        ram_bytes = psutil.virtual_memory().total
        profile.system_ram_mb = int(ram_bytes / (1024 * 1024))
        
        # Detect CPU
        cores = psutil.cpu_count(logical=False)
        if cores:
            profile.cpu_cores = cores

        # Attempt to detect GPU using nvidia-smi via subprocess
        import subprocess
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode == 0:
            vram_mb = int(result.stdout.strip())
            profile.gpu_vram_mb = vram_mb
            if vram_mb > 10000:
                profile.name = "high_end_gpu"
            else:
                profile.name = "mid_range_gpu"
                
    except Exception as e:
        logger.warning(f"Hardware detection incomplete, using SIH baseline: {e}")

    logger.info(f"Hardware Profile loaded: {profile.name} (VRAM: {profile.gpu_vram_mb}MB, RAM: {profile.system_ram_mb}MB)")
    return profile

# Singleton instance
current_hardware = detect_hardware()
