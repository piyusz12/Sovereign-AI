"""
Sovereign AI Workbench — Native C++ Fast Core Verification & Benchmarks

Validates:
1. Direct DXGI Hardware GPU VRAM & Memory Query
2. Win32 Job Objects Sandbox Enclave (Memory caps & CPU limits)
3. AVX2 + FMA SIMD Vector Engine (Numerical parity & Speedup)
4. Fast Multi-Pattern Zero-Egress Scanner
"""

import time
import math
import subprocess
import pytest
from backend.cpp_bridge.bridge import cpp_core


def test_native_core_initialized():
    """Verify that the 64-bit sovereign_core.dll is loaded and available."""
    assert cpp_core.is_available() is True, "64-bit sovereign_core.dll must be initialized"


def test_dxgi_hardware_query():
    """Verify direct DXGI hardware query of dedicated GPU VRAM and physical RAM."""
    hw = cpp_core.query_hardware()
    assert hw["source"] == "native_cpp_dxgi"
    assert hw["gpu_vram_mb"] > 0, "Dedicated GPU VRAM must be non-zero"
    assert hw["system_ram_mb"] > 0, "System RAM must be non-zero"
    assert hw["cpu_cores"] > 0, "CPU cores must be non-zero"
    assert len(hw["gpu_name"]) > 0, "GPU device name must be returned"
    print(f"\n[C++ Hardware Test] GPU: {hw['gpu_name']} | Dedicated VRAM: {hw['gpu_vram_mb']} MB | RAM: {hw['system_ram_mb']} MB")


def test_simd_dot_product_numerical_parity():
    """Verify AVX2 SIMD dot product matches mathematical sum for various dimensions."""
    dims = [8, 16, 64, 128, 768, 1536]
    for d in dims:
        a = [float(i) * 0.1 for i in range(d)]
        b = [float(i) * 0.2 for i in range(d)]

        expected = sum(x * y for x, y in zip(a, b))
        simd_result = cpp_core.simd_dot_product(a, b)

        assert math.isclose(simd_result, expected, rel_tol=1e-4), f"Mismatch at dim {d}: {simd_result} vs {expected}"


def test_simd_cosine_similarity():
    """Verify AVX2 SIMD cosine similarity."""
    a = [1.0, 0.0, 0.0, 1.0]
    b = [1.0, 0.0, 0.0, 1.0]
    c = [0.0, 1.0, 1.0, 0.0]

    assert math.isclose(cpp_core.simd_cosine_similarity(a, b), 1.0, rel_tol=1e-4)
    assert math.isclose(cpp_core.simd_cosine_similarity(a, c), 0.0, rel_tol=1e-4)


def test_simd_batch_topk_benchmark():
    """Benchmark AVX2 SIMD top-K search over 1,000 vectors vs pure Python."""
    num_vectors = 1000
    dim = 256
    query = [1.0 / math.sqrt(dim)] * dim
    matrix = [[(float(i + 1) * 0.001 + float(j + 1) * 0.0001) for j in range(dim)] for i in range(num_vectors)]

    # 1. Native C++ SIMD run
    start_simd = time.perf_counter()
    topk_simd = cpp_core.simd_batch_topk(query, matrix, top_k=5)
    simd_duration_ms = (time.perf_counter() - start_simd) * 1000

    # 2. Pure Python fallback run
    start_py = time.perf_counter()
    scores_py = []
    for i, vec in enumerate(matrix):
        dot = sum(x * y for x, y in zip(query, vec))
        norm_v = math.sqrt(sum(x * x for x in vec))
        sim = dot / norm_v if norm_v > 0 else 0.0
        scores_py.append((i, sim))
    scores_py.sort(key=lambda x: x[1], reverse=True)
    topk_py = scores_py[:5]
    py_duration_ms = (time.perf_counter() - start_py) * 1000

    print(f"\n[SIMD Vector Benchmark] Native AVX2: {simd_duration_ms:.2f}ms vs Python: {py_duration_ms:.2f}ms")
    print(f"Speedup: {py_duration_ms / max(simd_duration_ms, 0.001):.1f}x")

    assert len(topk_simd) == 5
    # Verify top score matches within float tolerance
    assert math.isclose(topk_simd[0][1], topk_py[0][1], rel_tol=1e-4)


def test_win32_job_enclave_containment():
    """Verify that native Win32 Job Object sandbox tracks memory and CPU of subprocess."""
    enclave = cpp_core.create_sandbox_enclave(max_memory_mb=256, max_processes=4, cpu_rate_percent=90)
    assert enclave is not None, "Failed to create Win32 Job Object enclave"

    p = subprocess.Popen(["python", "-c", "import time; x = [0]*100000; time.sleep(0.2)"])
    assigned = enclave.assign_process(p.pid)
    assert assigned is True, "Failed to assign process to Job Object"

    p.wait()
    stats = enclave.get_stats()
    enclave.close()

    assert stats["peak_memory_bytes"] > 0, "Peak memory must be recorded by kernel"
    print(f"\n[Sandbox Enclave Test] Peak RAM: {stats['peak_memory_mb']} MB | CPU Time: {stats['cpu_time_us']} us")


def test_fast_scanner():
    """Verify zero-copy pattern scanner matches forbidden egress tokens."""
    text = "The quick brown fox transmits confidential internal report to external server."
    patterns = ["confidential", "internal", "external", "secret_key", "password"]

    matches = cpp_core.fast_scan(text, patterns)
    assert "confidential" in matches
    assert "internal" in matches
    assert "external" in matches
    assert "secret_key" not in matches
    assert "password" not in matches
