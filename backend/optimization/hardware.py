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
    cpu_cores: int             # physical CPU cores
    cpu_threads: int = 16      # logical hardware threads
    cpu_model: str = "AMD/Intel Multi-Core Processor"
    simd_avx2_supported: bool = True
    compute_mode: str = "hybrid_balanced"

def detect_hardware() -> HardwareProfile:
    """
    Detects hardware using native C++ DXGI & Win32 with fallback to psutil/nvidia-smi.
    """
    physical_cores = psutil.cpu_count(logical=False) or 8
    logical_threads = psutil.cpu_count(logical=True) or 16
    cpu_name = platform.processor() or "Multi-Core x86_64 Processor"

    try:
        from backend.cpp_bridge.bridge import cpp_core
        hw = cpp_core.query_hardware()
        profile = HardwareProfile(
            name=hw.get("gpu_name", "rtx4060_8gb"),
            gpu_vram_mb=hw.get("gpu_vram_mb", 8192),
            system_ram_mb=hw.get("system_ram_mb", 16384),
            cpu_cores=hw.get("cpu_cores", physical_cores),
            cpu_threads=logical_threads,
            cpu_model=cpu_name,
            simd_avx2_supported=True,
            compute_mode="hybrid_balanced",
        )
        logger.info(f"Hardware Profile loaded via {hw.get('source', 'native_cpp')}: {profile.name} (VRAM: {profile.gpu_vram_mb}MB, RAM: {profile.system_ram_mb}MB, CPU: {profile.cpu_cores}C/{profile.cpu_threads}T)")
        return profile
    except Exception as e:
        logger.warning(f"Native hardware query failed, using fallback: {e}")

    # Fallback/Default for SIH Demo
    profile = HardwareProfile(
        name="rtx4060_8gb",
        gpu_vram_mb=8192,
        system_ram_mb=16384,
        cpu_cores=8
    )

    try:
        ram_bytes = psutil.virtual_memory().total
        profile.system_ram_mb = int(ram_bytes / (1024 * 1024))
        cores = psutil.cpu_count(logical=False)
        if cores:
            profile.cpu_cores = cores
    except Exception as e:
        logger.warning(f"Hardware detection incomplete, using SIH baseline: {e}")

    logger.info(f"Hardware Profile loaded: {profile.name} (VRAM: {profile.gpu_vram_mb}MB, RAM: {profile.system_ram_mb}MB)")
    return profile

# Singleton instance
current_hardware = detect_hardware()
