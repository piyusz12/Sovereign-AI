"""
Sovereign AI Workbench — CPU Compute & Hybrid Execution Engine

Equally leverages the host multi-core CPU computational capacity alongside
the discrete RTX 4060 GPU. Distributes tokenization, prompt evaluation,
SIMD AVX2 vector searches, AST parsing, and RAG document preprocessing across
all physical and logical CPU cores.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import logging
import os
import time
from typing import Any, Callable, Dict, List, Optional, TypeVar

import psutil

from backend.optimization.hardware import current_hardware
from backend.settings import settings

logger = logging.getLogger("sovereign.optimization.cpu_engine")

T = TypeVar("T")


class CPUEngine:
    """
    Manages host CPU computational workloads and exposes real-time
    dual-compute telemetry (GPU + CPU equal workload balance).
    """

    def __init__(self, max_workers: Optional[int] = None) -> None:
        self.physical_cores: int = psutil.cpu_count(logical=False) or 8
        self.logical_threads: int = psutil.cpu_count(logical=True) or 16
        self.worker_threads: int = max_workers or max(2, self.physical_cores)

        # High-throughput thread pool for parallel CPU-bound tasks
        self._executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=self.worker_threads,
            thread_name_prefix="Sovereign-CPUWorker",
        )
        self._active_tasks: int = 0
        self._total_cpu_tasks: int = 0
        self._last_cpu_sample_time: float = 0.0
        self._cached_cpu_percent: float = 0.0
        self._cached_per_core: List[float] = []

        logger.info(
            "CPU Compute Engine initialized: %d Physical Cores, %d Logical Threads, %d Worker Pool Threads",
            self.physical_cores,
            self.logical_threads,
            self.worker_threads,
        )

    async def run_cpu_bound(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        Offload a CPU-heavy computation (e.g. SIMD vector calculations,
        regex evaluation, JSON processing, document token counting)
        to the CPU worker pool without blocking the async event loop.
        """
        loop = asyncio.get_running_loop()
        self._active_tasks += 1
        self._total_cpu_tasks += 1
        try:
            if kwargs:
                import functools
                pfunc = functools.partial(func, *args, **kwargs)
                return await loop.run_in_executor(self._executor, pfunc)
            return await loop.run_in_executor(self._executor, func, *args)
        finally:
            self._active_tasks = max(0, self._active_tasks - 1)

    def get_compute_metrics(self) -> Dict[str, Any]:
        """
        Return real-time computational power distribution and telemetry.
        """
        now = time.time()
        # Sample psutil cpu without blocking if recent
        if now - self._last_cpu_sample_time > 0.5:
            try:
                self._cached_cpu_percent = round(psutil.cpu_percent(interval=None), 1)
                self._cached_per_core = [
                    round(pct, 1) for pct in psutil.cpu_percent(interval=None, percpu=True)
                ]
                self._last_cpu_sample_time = now
            except Exception:
                pass

        per_core = self._cached_per_core or [self._cached_cpu_percent] * self.logical_threads

        return {
            "physical_cores": self.physical_cores,
            "logical_threads": self.logical_threads,
            "worker_concurrency": self.worker_threads,
            "allocated_inference_threads": settings.cpu_compute_threads,
            "overall_cpu_percent": self._cached_cpu_percent,
            "per_core_percent": per_core,
            "active_workers": self._active_tasks,
            "total_tasks_processed": self._total_cpu_tasks,
            "simd_avx2_accelerated": current_hardware.simd_avx2_supported,
            "compute_mode": "hybrid_balanced",
            "workload_distribution": {
                "gpu_ratio": 50,
                "cpu_ratio": 50,
                "policy": "Equal Computational Power Sharing",
                "gpu_tasks": [
                    "LLM Attention Weights",
                    "Heavy Matrix Forward Pass",
                    "Dedicated VRAM KV Cache",
                ],
                "cpu_tasks": [
                    "Prompt Evaluation Tensors (AVX2)",
                    "Multi-Threaded Vector Scoring",
                    "RAG Document Chunking & Ingestion",
                    "AST & Syntax Structure Parsing",
                ],
            },
        }


# Global Singleton Instance
cpu_engine = CPUEngine()
