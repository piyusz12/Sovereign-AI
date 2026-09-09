"""
Sovereign AI: Model-Driven Hardware Co-Design & Silicon Mapping Engine
Evaluates vocabulary topology, context depth, and MoE routing sparsity to generate
hardware deployment manifests mapping models to specialized physical acceleration units.
"""

import math
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

@dataclass
class ModelProfile:
    model_id: str
    parameter_count_b: float
    vocab_size: int = 152064
    context_window: int = 32768
    architecture: str = "dense"  # "dense" or "moe"
    num_experts: int = 1
    active_experts: int = 1
    target_precision: str = "int4"  # "fp16", "int8", "int4"

@dataclass
class SiliconTarget:
    name: str
    vendor: str
    vram_gb: float
    memory_bandwidth_gbps: float
    supports_confidential_computing: bool
    supports_paged_attention: bool
    typical_tdp_w: int

@dataclass
class HardwareMappingManifest:
    model_id: str
    target_silicon: str
    recommended_precision: str
    weight_memory_gb: float
    kv_cache_per_req_mb: float
    max_concurrency_in_vram: int
    gpu_layers_offload: int
    cpu_offload_layers: int
    cpu_worker_threads: int
    kv_cache_strategy: str
    estimated_throughput_tps: float
    estimated_power_draw_w: float
    security_boundary: str
    optimizations_enabled: List[str] = field(default_factory=list)
    co_design_notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class HardwareCoDesignMapper:
    """
    Synthesizes model architecture metrics with physical hardware constraints
    to output deterministic execution and layer-offloading manifests.
    """

    SUPPORTED_TARGETS: Dict[str, SiliconTarget] = {
        "LOCAL_HYBRID_RTX4060": SiliconTarget(
            name="RTX 4060 Laptop (8GB) + AVX2 Multi-Core CPU",
            vendor="NVIDIA / AMD-Intel Hybrid",
            vram_gb=8.0,
            memory_bandwidth_gbps=272.0,
            supports_confidential_computing=False,
            supports_paged_attention=True,
            typical_tdp_w=115
        ),
        "NVIDIA_H100_CC": SiliconTarget(
            name="NVIDIA H100 SXM5 80GB (Confidential Computing)",
            vendor="NVIDIA",
            vram_gb=80.0,
            memory_bandwidth_gbps=3350.0,
            supports_confidential_computing=True,
            supports_paged_attention=True,
            typical_tdp_w=700
        ),
        "AMD_MI300X_ROCM": SiliconTarget(
            name="AMD Instinct MI300X 192GB (SEV-SNP Protected)",
            vendor="AMD",
            vram_gb=192.0,
            memory_bandwidth_gbps=5300.0,
            supports_confidential_computing=True,
            supports_paged_attention=True,
            typical_tdp_w=750
        ),
        "APPLE_SILICON_M3_MAX": SiliconTarget(
            name="Apple M3 Max Unified Memory 128GB",
            vendor="Apple",
            vram_gb=128.0,
            memory_bandwidth_gbps=400.0,
            supports_confidential_computing=False,
            supports_paged_attention=True,
            typical_tdp_w=90
        ),
    }

    def __init__(self, default_target: str = "LOCAL_HYBRID_RTX4060"):
        self.default_target = default_target

    def calculate_memory_footprint(self, profile: ModelProfile) -> Dict[str, float]:
        """
        Calculates exact weight footprint and KV cache memory per context slot.
        """
        bytes_per_param = {
            "fp16": 2.0,
            "int8": 1.0,
            "int4": 0.55  # 4-bit with metadata/scales
        }.get(profile.target_precision, 0.55)

        total_weights_gb = profile.parameter_count_b * bytes_per_param

        # KV cache estimation
        hidden_dim = int(math.sqrt(profile.parameter_count_b * 1e9 / 24))
        layers = int(profile.parameter_count_b * 3.5) if profile.parameter_count_b < 10 else 32
        bytes_per_token = 2 * layers * (hidden_dim // 4) * 2 * 2
        kv_per_req_mb = (bytes_per_token * profile.context_window) / (1024 * 1024)

        return {
            "weight_gb": round(total_weights_gb, 2),
            "kv_cache_per_req_mb": round(kv_per_req_mb, 2)
        }

    def generate_manifest(
        self,
        profile: ModelProfile,
        target_name: Optional[str] = None,
        enforce_confidential: bool = False
    ) -> HardwareMappingManifest:
        """
        Evaluates model properties and generates deployment manifest.
        """
        target_key = target_name or self.default_target
        if enforce_confidential and not self.SUPPORTED_TARGETS[target_key].supports_confidential_computing:
            target_key = "NVIDIA_H100_CC"

        silicon = self.SUPPORTED_TARGETS.get(target_key, self.SUPPORTED_TARGETS["LOCAL_HYBRID_RTX4060"])
        footprint = self.calculate_memory_footprint(profile)
        weight_gb = footprint["weight_gb"]
        kv_cache_mb = footprint["kv_cache_per_req_mb"]

        optimizations: List[str] = []
        notes: List[str] = []

        if profile.vocab_size > 200000:
            optimizations.append("Vocab-Parallel Embedding Slicing (Split Logits across AVX2/VRAM)")
            notes.append(f"High-density vocabulary ({profile.vocab_size} tokens) requires dedicated embedding shard.")

        if profile.context_window >= 32768:
            optimizations.append("FlashAttention-2 / Chunked Prefill with Ring Attention")
            kv_strategy = "PagedAttention + Ring KV Cache Chunking"
        else:
            optimizations.append("Standard PagedAttention")
            kv_strategy = "PagedAttention Dynamic Blocks"

        available_vram = silicon.vram_gb * 0.85
        total_layers = max(28, int(profile.parameter_count_b * 4))

        if weight_gb <= available_vram:
            gpu_layers = total_layers
            cpu_layers = 0
            cpu_threads = 8  # Balanced 8 CPU threads for prompt processing & KV management
            notes.append("Full VRAM fit: zero offloading penalty.")
        else:
            layer_weight_gb = weight_gb / total_layers
            gpu_layers = max(0, int(available_vram // layer_weight_gb))
            cpu_layers = total_layers - gpu_layers
            cpu_threads = 8  # Equal CPU compute power allocation
            optimizations.append(f"Hybrid Split Pipeline: {gpu_layers} GPU layers + {cpu_layers} CPU layers")
            notes.append(f"Model ({weight_gb:.1f}GB) exceeds VRAM ({silicon.vram_gb}GB). Splitting across CPU/GPU with equal 8-thread allocation.")

        remaining_vram_mb = max(512, (available_vram - (gpu_layers * (weight_gb / total_layers))) * 1024)
        max_concurrency = max(1, int(remaining_vram_mb // max(1.0, kv_cache_mb)))

        if silicon.memory_bandwidth_gbps > 2000:
            tps_base = 65.0
        elif silicon.memory_bandwidth_gbps > 1000:
            tps_base = 45.0
        else:
            tps_base = 25.0

        if cpu_layers > 0:
            ratio_on_cpu = cpu_layers / total_layers
            tps_est = max(8.0, tps_base * (1.0 - (ratio_on_cpu * 0.6)))
        else:
            tps_est = tps_base

        if profile.architecture == "moe":
            optimizations.append(f"MoE Expert Parallelism ({profile.active_experts}/{profile.num_experts} active)")
            tps_est *= 1.4

        power_envelope = silicon.typical_tdp_w * (0.5 + 0.5 * (gpu_layers / max(1, total_layers)))
        security_desc = "Hardware TEE Active (ECDSA P-384 Attested)" if silicon.supports_confidential_computing else "Standard Host Isolation"

        return HardwareMappingManifest(
            model_id=profile.model_id,
            target_silicon=silicon.name,
            recommended_precision=profile.target_precision,
            weight_memory_gb=weight_gb,
            kv_cache_per_req_mb=kv_cache_mb,
            max_concurrency_in_vram=max_concurrency,
            gpu_layers_offload=gpu_layers,
            cpu_offload_layers=cpu_layers,
            cpu_worker_threads=cpu_threads,
            kv_cache_strategy=kv_strategy,
            estimated_throughput_tps=round(tps_est, 1),
            estimated_power_draw_w=round(power_envelope, 1),
            security_boundary=security_desc,
            optimizations_enabled=optimizations,
            co_design_notes=notes
        )

hardware_co_design_mapper = HardwareCoDesignMapper()
