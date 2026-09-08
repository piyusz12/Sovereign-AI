# -*- coding: utf-8 -*-
"""
Sovereign AI Workbench - C++ Fast Core Bridge (ctypes)

Connects Python orchestration to the compiled 64-bit C++ sovereign_core.dll for:
1. Hardware Control: Microsecond DXGI GPU VRAM & system memory queries
2. Memory Management: Win32 Job Objects sandbox enclaves with 512MB hard caps
3. Raw Speed: AVX2 + FMA SIMD vector dot product, cosine distance, and batch top-K search
4. Zero-Egress Security: High-speed multi-pattern memory and egress packet scanner
5. Model Management: Sub-millisecond routing, VRAM safety gates, and firewall evaluation
"""

from __future__ import annotations

import array
import ctypes
import logging
import math
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("sovereign.cpp_bridge")

TASK_TYPE_NAMES = [
    "reasoning",
    "coding",
    "vision",
    "document_reasoning",
    "data_analysis",
    "general",
]

POLICY_NAMES = [
    "allowed",
    "approval_required",
    "blocked",
]


class NativeSandboxEnclave:
    """Wrapper around a native Win32 Job Object sandbox handle."""

    def __init__(self, core: "CppCore", handle: Any, max_memory_bytes: int):
        self._core = core
        self._handle = handle
        self._max_memory_bytes = max_memory_bytes

    def assign_process(self, process_handle_or_pid: Any) -> bool:
        if not self._handle or not self._core._dll:
            return False

        # If integer PID is passed on Windows, open process handle with required rights
        if isinstance(process_handle_or_pid, int):
            kernel32 = ctypes.windll.kernel32
            PROCESS_SET_QUOTA = 0x0100
            PROCESS_TERMINATE = 0x0001
            h_proc = kernel32.OpenProcess(PROCESS_SET_QUOTA | PROCESS_TERMINATE, False, process_handle_or_pid)
            if not h_proc:
                return False
            success = bool(self._core._dll.sovereign_sandbox_assign(self._handle, ctypes.c_void_p(h_proc)))
            kernel32.CloseHandle(h_proc)
            return success

        return bool(self._core._dll.sovereign_sandbox_assign(self._handle, ctypes.c_void_p(process_handle_or_pid)))

    def get_stats(self) -> Dict[str, Any]:
        if not self._handle or not self._core._dll:
            return {"peak_memory_bytes": 0, "cpu_time_us": 0, "active_processes": 0}

        peak_mem = ctypes.c_size_t(0)
        cpu_time = ctypes.c_uint64(0)
        procs = ctypes.c_uint32(0)

        res = self._core._dll.sovereign_sandbox_get_stats(
            self._handle,
            ctypes.byref(peak_mem),
            ctypes.byref(cpu_time),
            ctypes.byref(procs),
        )
        if res == 0:
            return {
                "peak_memory_bytes": peak_mem.value,
                "peak_memory_mb": round(peak_mem.value / (1024 * 1024), 2),
                "cpu_time_us": cpu_time.value,
                "active_processes": procs.value,
            }
        return {"peak_memory_bytes": 0, "cpu_time_us": 0, "active_processes": 0}

    def terminate(self, exit_code: int = 1) -> bool:
        if not self._handle or not self._core._dll:
            return False
        return bool(self._core._dll.sovereign_sandbox_terminate(self._handle, ctypes.c_uint32(exit_code)))

    def close(self):
        if self._handle and self._core._dll:
            self._core._dll.sovereign_sandbox_close(self._handle)
            self._handle = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class CppCore:
    def __init__(self):
        self._dll: Optional[ctypes.CDLL] = None
        self._available = False
        self._active_model = ""
        self._load_dll()

    def _load_dll(self):
        base_dir = Path(__file__).resolve().parent.parent.parent
        dll_path = base_dir / "cpp-core" / "build" / "sovereign_core.dll"

        if not dll_path.exists():
            logger.debug("sovereign_core.dll not found at %s. Fast C++ path disabled.", dll_path)
            return

        try:
            self._dll = ctypes.CDLL(str(dll_path))

            # Core Init
            self._dll.sovereign_core_init.restype = ctypes.c_int
            self._dll.sovereign_core_init.argtypes = []

            # Router
            self._dll.sovereign_router_classify.restype = ctypes.c_int
            self._dll.sovereign_router_classify.argtypes = [
                ctypes.c_char_p,
                ctypes.c_int,
                ctypes.POINTER(ctypes.c_int),
                ctypes.c_char_p,
                ctypes.c_int,
                ctypes.POINTER(ctypes.c_float),
            ]

            # Memory
            self._dll.sovereign_memory_can_load.restype = ctypes.c_int
            self._dll.sovereign_memory_can_load.argtypes = [ctypes.c_char_p, ctypes.c_int64]

            self._dll.sovereign_memory_prepare_switch.restype = ctypes.c_int
            self._dll.sovereign_memory_prepare_switch.argtypes = [
                ctypes.c_char_p,
                ctypes.c_int64,
                ctypes.c_char_p,
                ctypes.c_int,
            ]

            self._dll.sovereign_memory_record_loaded.restype = None
            self._dll.sovereign_memory_record_loaded.argtypes = [ctypes.c_char_p, ctypes.c_int64]

            self._dll.sovereign_memory_record_unloaded.restype = None
            self._dll.sovereign_memory_record_unloaded.argtypes = [ctypes.c_char_p]

            # Firewall
            self._dll.sovereign_firewall_evaluate.restype = ctypes.c_int
            self._dll.sovereign_firewall_evaluate.argtypes = [
                ctypes.c_char_p,
                ctypes.c_char_p,
                ctypes.POINTER(ctypes.c_int),
                ctypes.c_char_p,
                ctypes.c_int,
            ]

            # Prompt
            self._dll.sovereign_prompt_estimate_tokens.restype = ctypes.c_size_t
            self._dll.sovereign_prompt_estimate_tokens.argtypes = [ctypes.c_char_p]

            # Hardware Control
            self._dll.sovereign_hardware_query.restype = ctypes.c_int
            self._dll.sovereign_hardware_query.argtypes = [
                ctypes.POINTER(ctypes.c_uint64),
                ctypes.POINTER(ctypes.c_uint64),
                ctypes.POINTER(ctypes.c_uint64),
                ctypes.POINTER(ctypes.c_uint64),
                ctypes.POINTER(ctypes.c_uint32),
                ctypes.c_wchar_p,
                ctypes.c_int,
            ]

            # Sandbox Enclave
            self._dll.sovereign_sandbox_create.restype = ctypes.c_void_p
            self._dll.sovereign_sandbox_create.argtypes = [
                ctypes.c_size_t,
                ctypes.c_uint32,
                ctypes.c_uint32,
            ]

            self._dll.sovereign_sandbox_assign.restype = ctypes.c_int
            self._dll.sovereign_sandbox_assign.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

            self._dll.sovereign_sandbox_get_stats.restype = ctypes.c_int
            self._dll.sovereign_sandbox_get_stats.argtypes = [
                ctypes.c_void_p,
                ctypes.POINTER(ctypes.c_size_t),
                ctypes.POINTER(ctypes.c_uint64),
                ctypes.POINTER(ctypes.c_uint32),
            ]

            self._dll.sovereign_sandbox_terminate.restype = ctypes.c_int
            self._dll.sovereign_sandbox_terminate.argtypes = [ctypes.c_void_p, ctypes.c_uint32]

            self._dll.sovereign_sandbox_close.restype = None
            self._dll.sovereign_sandbox_close.argtypes = [ctypes.c_void_p]

            # SIMD Vector Engine
            self._dll.sovereign_simd_dot.restype = ctypes.c_float
            self._dll.sovereign_simd_dot.argtypes = [
                ctypes.POINTER(ctypes.c_float),
                ctypes.POINTER(ctypes.c_float),
                ctypes.c_int,
            ]

            self._dll.sovereign_simd_cosine.restype = ctypes.c_float
            self._dll.sovereign_simd_cosine.argtypes = [
                ctypes.POINTER(ctypes.c_float),
                ctypes.POINTER(ctypes.c_float),
                ctypes.c_int,
            ]

            self._dll.sovereign_simd_batch_topk.restype = ctypes.c_int
            self._dll.sovereign_simd_batch_topk.argtypes = [
                ctypes.POINTER(ctypes.c_float),
                ctypes.POINTER(ctypes.c_float),
                ctypes.c_int,
                ctypes.c_int,
                ctypes.c_int,
                ctypes.POINTER(ctypes.c_int),
                ctypes.POINTER(ctypes.c_float),
            ]

            # Fast Scanner
            self._dll.sovereign_fast_scan.restype = ctypes.c_int
            self._dll.sovereign_fast_scan.argtypes = [
                ctypes.c_char_p,
                ctypes.c_size_t,
                ctypes.POINTER(ctypes.c_char_p),
                ctypes.c_int,
                ctypes.POINTER(ctypes.c_int),
                ctypes.c_int,
            ]

            init_res = self._dll.sovereign_core_init()
            if init_res == 0:
                self._available = True
                logger.info("Successfully initialized Sovereign C++ Fast Core (sovereign_core.dll)")
            else:
                logger.warning("sovereign_core_init returned non-zero: %d", init_res)

        except Exception as e:
            logger.info("Operating in Python Fast Core mode: %s", e)
            self._dll = None
            self._available = False

    def is_available(self) -> bool:
        return self._available

    # ─────────────────────────────────────────────────────────────────────────
    # Hardware Control
    # ─────────────────────────────────────────────────────────────────────────

    def query_hardware(self) -> Dict[str, Any]:
        """
        Direct hardware query via DirectX Graphics Infrastructure (DXGI) & Win32.
        Microsecond execution without spawning slow subprocesses.
        """
        if self._available and self._dll:
            vram_bytes = ctypes.c_uint64(0)
            shared_bytes = ctypes.c_uint64(0)
            total_ram = ctypes.c_uint64(0)
            avail_ram = ctypes.c_uint64(0)
            cores = ctypes.c_uint32(0)
            name_buf = ctypes.create_unicode_buffer(256)

            res = self._dll.sovereign_hardware_query(
                ctypes.byref(vram_bytes),
                ctypes.byref(shared_bytes),
                ctypes.byref(total_ram),
                ctypes.byref(avail_ram),
                ctypes.byref(cores),
                name_buf,
                256,
            )
            if res == 0:
                vram_mb = int(vram_bytes.value // (1024 * 1024))
                return {
                    "source": "native_cpp_dxgi",
                    "gpu_name": name_buf.value or "Dedicated Local GPU",
                    "gpu_vram_mb": vram_mb,
                    "shared_vram_mb": int(shared_bytes.value // (1024 * 1024)),
                    "system_ram_mb": int(total_ram.value // (1024 * 1024)),
                    "available_ram_mb": int(avail_ram.value // (1024 * 1024)),
                    "cpu_cores": int(cores.value),
                    "is_discrete_gpu": vram_mb > 512,
                }

        # Python Fallback
        import psutil
        ram_mb = int(psutil.virtual_memory().total / (1024 * 1024))
        return {
            "source": "python_psutil_fallback",
            "gpu_name": "Local RTX GPU (8GB)",
            "gpu_vram_mb": 8192,
            "shared_vram_mb": 4096,
            "system_ram_mb": ram_mb,
            "available_ram_mb": int(psutil.virtual_memory().available / (1024 * 1024)),
            "cpu_cores": psutil.cpu_count(logical=False) or 8,
            "is_discrete_gpu": True,
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Sandbox Enclave (Win32 Job Objects)
    # ─────────────────────────────────────────────────────────────────────────

    def create_sandbox_enclave(
        self,
        max_memory_mb: int = 512,
        max_processes: int = 8,
        cpu_rate_percent: int = 80,
    ) -> Optional[NativeSandboxEnclave]:
        """
        Creates an isolated native Win32 Job Object sandbox enclave.
        Enforces hard memory limit (OS memory exception if breached),
        CPU cycle rate cap, and active process count.
        """
        if self._available and self._dll:
            mem_bytes = max_memory_mb * 1024 * 1024
            handle = self._dll.sovereign_sandbox_create(
                ctypes.c_size_t(mem_bytes),
                ctypes.c_uint32(max_processes),
                ctypes.c_uint32(cpu_rate_percent),
            )
            if handle:
                return NativeSandboxEnclave(self, handle, mem_bytes)
        return None

    # ─────────────────────────────────────────────────────────────────────────
    # AVX2 SIMD Vector Similarity Engine
    # ─────────────────────────────────────────────────────────────────────────

    def simd_dot_product(self, a: List[float], b: List[float]) -> float:
        """AVX2 SIMD dot product of two float vectors."""
        dim = len(a)
        if dim == 0 or dim != len(b):
            return 0.0

        if self._available and self._dll:
            arr_a = (ctypes.c_float * dim)(*a)
            arr_b = (ctypes.c_float * dim)(*b)
            return float(self._dll.sovereign_simd_dot(arr_a, arr_b, dim))

        return sum(x * y for x, y in zip(a, b))

    def simd_cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """AVX2 SIMD cosine similarity of two float vectors."""
        dim = len(a)
        if dim == 0 or dim != len(b):
            return 0.0

        if self._available and self._dll:
            arr_a = (ctypes.c_float * dim)(*a)
            arr_b = (ctypes.c_float * dim)(*b)
            return float(self._dll.sovereign_simd_cosine(arr_a, arr_b, dim))

        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a <= 1e-9 or norm_b <= 1e-9:
            return 0.0
        return sum(x * y for x, y in zip(a, b)) / (norm_a * norm_b)

    def simd_batch_topk(
        self,
        query: List[float],
        matrix: List[List[float]],
        top_k: int = 5,
    ) -> List[Tuple[int, float]]:
        """
        AVX2 SIMD batch top-K similarity search.
        Searches query vector against matrix of document vectors in native C++.
        Returns list of (index, similarity_score).
        """
        num_vectors = len(matrix)
        if num_vectors == 0 or not query:
            return []

        dim = len(query)
        top_k = min(top_k, num_vectors)

        if self._available and self._dll:
            flat_matrix = [val for vec in matrix for val in vec]
            q_arr = array.array('f', query)
            m_arr = array.array('f', flat_matrix)
            arr_query = (ctypes.c_float * dim).from_buffer(q_arr)
            arr_matrix = (ctypes.c_float * len(flat_matrix)).from_buffer(m_arr)
            out_indices = (ctypes.c_int * top_k)()
            out_scores = (ctypes.c_float * top_k)()

            count = self._dll.sovereign_simd_batch_topk(
                arr_query,
                arr_matrix,
                num_vectors,
                dim,
                top_k,
                out_indices,
                out_scores,
            )
            return [(out_indices[i], float(out_scores[i])) for i in range(count)]

        # Python fallback
        scores = []
        for i, doc_vec in enumerate(matrix):
            sim = self.simd_cosine_similarity(query, doc_vec)
            scores.append((i, sim))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    # ─────────────────────────────────────────────────────────────────────────
    # Zero-Egress Scanner
    # ─────────────────────────────────────────────────────────────────────────

    def fast_scan(self, text: str, patterns: List[str]) -> List[str]:
        """
        Zero-copy fast substring scanning for forbidden keywords or egress data.
        Returns matched patterns.
        """
        if not text or not patterns:
            return []

        if self._available and self._dll:
            c_data = text.encode("utf-8")
            c_pats = (ctypes.c_char_p * len(patterns))(*[p.encode("utf-8") for p in patterns])
            out_matches = (ctypes.c_int * len(patterns))()

            count = self._dll.sovereign_fast_scan(
                c_data,
                len(c_data),
                c_pats,
                len(patterns),
                out_matches,
                len(patterns),
            )
            return [patterns[out_matches[i]] for i in range(count)]

        # Python fallback
        return [p for p in patterns if p in text]

    # ─────────────────────────────────────────────────────────────────────────
    # Classification & Routing
    # ─────────────────────────────────────────────────────────────────────────

    def classify(self, message: str, has_image: bool = False) -> Tuple[str, str, float, str]:
        """
        Fast zero-alloc task classification.
        Returns (task_type_str, model_name, confidence, reason).
        """
        if self._available and self._dll:
            out_task_type = ctypes.c_int(-1)
            out_model_buf = ctypes.create_string_buffer(64)
            out_confidence = ctypes.c_float(0.0)

            res = self._dll.sovereign_router_classify(
                message.encode("utf-8"),
                1 if has_image else 0,
                ctypes.byref(out_task_type),
                out_model_buf,
                64,
                ctypes.byref(out_confidence),
            )
            if res == 0:
                tt_idx = out_task_type.value
                task_name = TASK_TYPE_NAMES[tt_idx] if 0 <= tt_idx < len(TASK_TYPE_NAMES) else "reasoning"
                model_name = out_model_buf.value.decode("utf-8")
                conf = float(out_confidence.value)
                return task_name, model_name, conf, "C++ Fast Router heuristic classification"

        # Python Fast Path Fallback
        if has_image:
            return "vision", "qwen3-vl-8b", 0.95, "Image attached to request"

        lower = message.lower()
        code_kws = ["def ", "class ", "function", "write code", "python", "javascript", "typescript", "rust", "c++", "cpp", "java", "sql", "bug", "traceback", "refactor", "pytest", "script", "algorithm"]
        for kw in code_kws:
            if kw in lower:
                return "coding", "qwen2.5-coder-7b", 0.90, "Strong coding intent detected"

        vision_kws = ["inspect this image", "look at this diagram", "p&id", "schematic", "ocr", "chart", "plot", "screenshot", "visual"]
        for kw in vision_kws:
            if kw in lower:
                return "vision", "qwen3-vl-8b", 0.85, "Visual inspection keyword pattern"

        doc_kws = ["summarize document", "according to the manual", "inspection report", "sop", "policy", "purchase order", "invoice", "specification", "search documents", "rag"]
        for kw in doc_kws:
            if kw in lower:
                return "document_reasoning", "qwen3-14b", 0.85, "Enterprise document reasoning query"

        data_kws = ["pandas", "dataframe", "csv", "excel", "xlsx", "aggregate", "forecast", "statistics"]
        for kw in data_kws:
            if kw in lower:
                return "data_analysis", "qwen2.5-coder-7b", 0.80, "Data analysis / tabular processing"

        return "reasoning", "qwen3-14b", 0.70, "Default multi-step reasoning"

    # ─────────────────────────────────────────────────────────────────────────
    # Memory Switching & Safety
    # ─────────────────────────────────────────────────────────────────────────

    def memory_prepare_switch(self, target_model_id: str, required_vram_mb: int = 5500) -> Tuple[bool, str]:
        if self._available and self._dll:
            out_evict_buf = ctypes.create_string_buffer(64)
            allowed = self._dll.sovereign_memory_prepare_switch(
                target_model_id.encode("utf-8"),
                ctypes.c_int64(required_vram_mb),
                out_evict_buf,
                64,
            )
            evict_model = out_evict_buf.value.decode("utf-8")
            return bool(allowed), evict_model

        evict = ""
        if self._active_model and self._active_model != target_model_id:
            evict = self._active_model
        return True, evict

    def record_model_loaded(self, model_id: str, allocated_vram_mb: int = 5500):
        self._active_model = model_id
        if self._available and self._dll:
            self._dll.sovereign_memory_record_loaded(model_id.encode("utf-8"), ctypes.c_int64(allocated_vram_mb))

    def record_model_unloaded(self, model_id: str):
        if self._active_model == model_id:
            self._active_model = ""
        if self._available and self._dll:
            self._dll.sovereign_memory_record_unloaded(model_id.encode("utf-8"))

    # ─────────────────────────────────────────────────────────────────────────
    # Action Firewall
    # ─────────────────────────────────────────────────────────────────────────

    def firewall_evaluate(self, action: str, user_role: str = "engineering") -> Tuple[str, str, bool]:
        if self._available and self._dll:
            out_policy = ctypes.c_int(-1)
            out_reason_buf = ctypes.create_string_buffer(256)

            compliant = self._dll.sovereign_firewall_evaluate(
                action.encode("utf-8"),
                user_role.encode("utf-8"),
                ctypes.byref(out_policy),
                out_reason_buf,
                256,
            )
            pol_idx = out_policy.value
            policy_name = POLICY_NAMES[pol_idx] if 0 <= pol_idx < len(POLICY_NAMES) else "blocked"
            reason = out_reason_buf.value.decode("utf-8")
            return policy_name, reason, bool(compliant)

        if action in ["send_external", "network_request", "external_connect"]:
            return "blocked", "SOVEREIGNTY VIOLATION: External network requests are strictly forbidden.", False
        if action in ["delete_file", "modify_config", "install_package"]:
            return "approval_required", "Destructive or system modification action requires explicit operator approval.", True
        return "allowed", "Operation allowed under sovereign local security policy.", True

    def estimate_tokens(self, text: str) -> int:
        if self._available and self._dll:
            return int(self._dll.sovereign_prompt_estimate_tokens(text.encode("utf-8")))
        return (len(text or "") + 3) // 4


cpp_core = CppCore()
