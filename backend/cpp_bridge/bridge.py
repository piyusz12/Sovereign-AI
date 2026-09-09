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


# Win32 Type Definitions for direct OS C-ABI calls
if os.name == "nt":
    from ctypes import wintypes

    class _GUID(ctypes.Structure):
        _fields_ = [
            ("Data1", ctypes.c_ulong),
            ("Data2", ctypes.c_ushort),
            ("Data3", ctypes.c_ushort),
            ("Data4", ctypes.c_ubyte * 8),
        ]

    class _DXGI_ADAPTER_DESC(ctypes.Structure):
        _fields_ = [
            ("Description", wintypes.WCHAR * 128),
            ("VendorId", wintypes.UINT),
            ("DeviceId", wintypes.UINT),
            ("SubSysId", wintypes.UINT),
            ("Revision", wintypes.UINT),
            ("DedicatedVideoMemory", ctypes.c_size_t),
            ("DedicatedSystemMemory", ctypes.c_size_t),
            ("SharedSystemMemory", ctypes.c_size_t),
            ("AdapterLuid_LowPart", wintypes.DWORD),
            ("AdapterLuid_HighPart", wintypes.LONG),
        ]

    class _MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [
            ("dwLength", wintypes.DWORD),
            ("dwMemoryLoad", wintypes.DWORD),
            ("ullTotalPhys", ctypes.c_uint64),
            ("ullAvailPhys", ctypes.c_uint64),
            ("ullTotalPageFile", ctypes.c_uint64),
            ("ullAvailPageFile", ctypes.c_uint64),
            ("ullTotalVirtual", ctypes.c_uint64),
            ("ullAvailVirtual", ctypes.c_uint64),
            ("ullAvailExtendedVirtual", ctypes.c_uint64),
        ]

    class _IO_COUNTERS(ctypes.Structure):
        _fields_ = [
            ("ReadOperationCount", ctypes.c_uint64),
            ("WriteOperationCount", ctypes.c_uint64),
            ("OtherOperationCount", ctypes.c_uint64),
            ("ReadTransferCount", ctypes.c_uint64),
            ("WriteTransferCount", ctypes.c_uint64),
            ("OtherTransferCount", ctypes.c_uint64),
        ]

    class _JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", ctypes.c_int64),
            ("PerJobUserTimeLimit", ctypes.c_int64),
            ("LimitFlags", wintypes.DWORD),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", wintypes.DWORD),
            ("Affinity", ctypes.c_size_t),
            ("PriorityClass", wintypes.DWORD),
            ("SchedulingClass", wintypes.DWORD),
        ]

    class _JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", _JOBOBJECT_BASIC_LIMIT_INFORMATION),
            ("IoInfo", _IO_COUNTERS),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    class _JOBOBJECT_BASIC_ACCOUNTING_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("TotalUserTime", ctypes.c_int64),
            ("TotalKernelTime", ctypes.c_int64),
            ("ThisPeriodTotalUserTime", ctypes.c_int64),
            ("ThisPeriodTotalKernelTime", ctypes.c_int64),
            ("TotalPageFaultCount", wintypes.DWORD),
            ("TotalProcesses", wintypes.DWORD),
            ("ActiveProcesses", wintypes.DWORD),
            ("TotalTerminatedProcesses", wintypes.DWORD),
        ]

    class _JOBOBJECT_CPU_RATE_CONTROL_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("ControlFlags", wintypes.DWORD),
            ("CpuRate", wintypes.DWORD),
        ]


class NativeSandboxEnclave:
    """Wrapper around a native Win32 Job Object sandbox handle."""

    def __init__(
        self,
        core: "CppCore",
        handle: Any,
        max_memory_bytes: int,
        is_direct_win32: bool = False,
    ):
        self._core = core
        self._handle = handle
        self._max_memory_bytes = max_memory_bytes
        self._is_direct_win32 = is_direct_win32

    def assign_process(self, process_handle_or_pid: Any) -> bool:
        if not self._handle:
            return False

        if self._is_direct_win32:
            kernel32 = ctypes.windll.kernel32
            if isinstance(process_handle_or_pid, int):
                PROCESS_SET_QUOTA = 0x0100
                PROCESS_TERMINATE = 0x0001
                h_proc = kernel32.OpenProcess(PROCESS_SET_QUOTA | PROCESS_TERMINATE, False, process_handle_or_pid)
                if not h_proc:
                    return False
                success = bool(kernel32.AssignProcessToJobObject(self._handle, h_proc))
                kernel32.CloseHandle(h_proc)
                return success
            return bool(kernel32.AssignProcessToJobObject(self._handle, process_handle_or_pid))

        if not self._core._dll:
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
        if not self._handle:
            return {"peak_memory_bytes": 0, "peak_memory_mb": 0.0, "cpu_time_us": 0, "active_processes": 0}

        if self._is_direct_win32:
            kernel32 = ctypes.windll.kernel32
            query_ext = _JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
            res_ext = kernel32.QueryInformationJobObject(
                self._handle, 9, ctypes.byref(query_ext), ctypes.sizeof(query_ext), None
            )
            query_basic = _JOBOBJECT_BASIC_ACCOUNTING_INFORMATION()
            res_basic = kernel32.QueryInformationJobObject(
                self._handle, 1, ctypes.byref(query_basic), ctypes.sizeof(query_basic), None
            )
            peak_bytes = query_ext.PeakJobMemoryUsed if res_ext else 0
            cpu_us = ((query_basic.TotalKernelTime + query_basic.TotalUserTime) // 10) if res_basic else 0
            active_p = query_basic.ActiveProcesses if res_basic else 0
            return {
                "peak_memory_bytes": peak_bytes,
                "peak_memory_mb": round(peak_bytes / (1024 * 1024), 2),
                "cpu_time_us": cpu_us,
                "active_processes": active_p,
            }

        if not self._core._dll:
            return {"peak_memory_bytes": 0, "peak_memory_mb": 0.0, "cpu_time_us": 0, "active_processes": 0}

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
        return {"peak_memory_bytes": 0, "peak_memory_mb": 0.0, "cpu_time_us": 0, "active_processes": 0}

    def terminate(self, exit_code: int = 1) -> bool:
        if not self._handle:
            return False
        if self._is_direct_win32:
            return bool(ctypes.windll.kernel32.TerminateJobObject(self._handle, exit_code))
        if not self._core._dll:
            return False
        return bool(self._core._dll.sovereign_sandbox_terminate(self._handle, ctypes.c_uint32(exit_code)))

    def close(self):
        if self._handle:
            if self._is_direct_win32:
                ctypes.windll.kernel32.CloseHandle(self._handle)
            elif self._core._dll:
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

    def is_win32_native_available(self) -> bool:
        """Returns True if Windows native DXGI and Win32 Job Object capabilities are active."""
        return os.name == "nt"

    # ─────────────────────────────────────────────────────────────────────────
    # Hardware Control
    # ─────────────────────────────────────────────────────────────────────────

    def _query_dxgi_win32(self) -> Optional[Dict[str, Any]]:
        """
        Direct hardware query via DirectX Graphics Infrastructure (DXGI) and Win32 APIs.
        Queries the real discrete GPU (VRAM and shared memory) and physical RAM with microsecond latency.
        """
        if os.name != "nt":
            return None

        try:
            kernel32 = ctypes.windll.kernel32
            dxgi = ctypes.windll.dxgi

            # 1. System RAM via GlobalMemoryStatusEx
            mem_status = _MEMORYSTATUSEX()
            mem_status.dwLength = ctypes.sizeof(_MEMORYSTATUSEX)
            total_ram_mb = 0
            avail_ram_mb = 0
            if kernel32.GlobalMemoryStatusEx(ctypes.byref(mem_status)):
                total_ram_mb = int(mem_status.ullTotalPhys // (1024 * 1024))
                avail_ram_mb = int(mem_status.ullAvailPhys // (1024 * 1024))

            # 2. CPU Cores
            cpu_cores = os.cpu_count() or 8

            # 3. GPU VRAM & Model via DXGI COM interface
            iid_factory = _GUID(
                0x7B7166EC,
                0x21C7,
                0x44AE,
                (ctypes.c_ubyte * 8)(0xB2, 0x1A, 0xC9, 0xAE, 0x32, 0x1A, 0xE3, 0x69),
            )
            p_factory = ctypes.c_void_p()
            hr = dxgi.CreateDXGIFactory(ctypes.byref(iid_factory), ctypes.byref(p_factory))
            if hr != 0 or not p_factory.value:
                return None

            best_vram = -1
            best_shared = 0
            best_name = ""

            try:
                vtbl_factory = ctypes.cast(
                    p_factory, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))
                ).contents
                EnumAdapters_proto = ctypes.WINFUNCTYPE(
                    ctypes.c_long,
                    ctypes.c_void_p,
                    wintypes.UINT,
                    ctypes.POINTER(ctypes.c_void_p),
                )
                EnumAdapters = EnumAdapters_proto(vtbl_factory[7])

                adapter_idx = 0
                while True:
                    p_adapter = ctypes.c_void_p()
                    if EnumAdapters(p_factory, adapter_idx, ctypes.byref(p_adapter)) != 0:
                        break

                    vtbl_adapter = ctypes.cast(
                        p_adapter, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))
                    ).contents
                    GetDesc_proto = ctypes.WINFUNCTYPE(
                        ctypes.c_long,
                        ctypes.c_void_p,
                        ctypes.POINTER(_DXGI_ADAPTER_DESC),
                    )
                    GetDesc = GetDesc_proto(vtbl_adapter[8])
                    Release_proto = ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.c_void_p)
                    Release = Release_proto(vtbl_adapter[2])

                    desc = _DXGI_ADAPTER_DESC()
                    if GetDesc(p_adapter, ctypes.byref(desc)) == 0:
                        vram = desc.DedicatedVideoMemory
                        # Select discrete GPU with largest dedicated VRAM
                        if vram > best_vram or not best_name:
                            best_vram = vram
                            best_shared = desc.SharedSystemMemory
                            best_name = desc.Description

                    Release(p_adapter)
                    adapter_idx += 1

            finally:
                vtbl_factory = ctypes.cast(
                    p_factory, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))
                ).contents
                Release_proto = ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.c_void_p)
                Release_factory = Release_proto(vtbl_factory[2])
                Release_factory(p_factory)

            vram_mb = int(best_vram // (1024 * 1024)) if best_vram > 0 else 0
            shared_mb = int(best_shared // (1024 * 1024)) if best_shared > 0 else 0

            return {
                "source": "native_cpp_dxgi",
                "gpu_name": best_name or "DirectX Graphics Device",
                "gpu_vram_mb": vram_mb,
                "shared_vram_mb": shared_mb,
                "system_ram_mb": total_ram_mb,
                "available_ram_mb": avail_ram_mb,
                "cpu_cores": cpu_cores,
                "is_discrete_gpu": vram_mb > 512,
            }
        except Exception as exc:
            logger.debug("Native Win32 DXGI query failed: %s", exc)
            return None

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

        # Native DXGI query on Windows when DLL is uncompiled
        win32_hw = self._query_dxgi_win32()
        if win32_hw is not None:
            return win32_hw

        # Python Fallback for non-Windows platforms
        import psutil
        ram_mb = int(psutil.virtual_memory().total / (1024 * 1024))
        return {
            "source": "python_psutil_fallback",
            "gpu_name": "Local Discrete GPU",
            "gpu_vram_mb": 6144,
            "shared_vram_mb": 4096,
            "system_ram_mb": ram_mb,
            "available_ram_mb": int(psutil.virtual_memory().available / (1024 * 1024)),
            "cpu_cores": psutil.cpu_count(logical=False) or 8,
            "is_discrete_gpu": True,
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Sandbox Enclave (Win32 Job Objects)
    # ─────────────────────────────────────────────────────────────────────────

    def _create_win32_job_enclave(
        self,
        max_memory_mb: int = 512,
        max_processes: int = 8,
        cpu_rate_percent: int = 80,
    ) -> Optional[NativeSandboxEnclave]:
        """Creates a Win32 Job Object sandbox enclave via direct OS C-ABI calls."""
        if os.name != "nt":
            return None

        try:
            kernel32 = ctypes.windll.kernel32
            h_job = kernel32.CreateJobObjectW(None, None)
            if not h_job:
                return None

            mem_bytes = max_memory_mb * 1024 * 1024
            jeli = _JOBOBJECT_EXTENDED_LIMIT_INFORMATION()

            JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000
            JOB_OBJECT_LIMIT_DIE_ON_UNHANDLED_EXCEPTION = 0x0400
            JOB_OBJECT_LIMIT_PROCESS_MEMORY = 0x0100
            JOB_OBJECT_LIMIT_JOB_MEMORY = 0x0200
            JOB_OBJECT_LIMIT_ACTIVE_PROCESS = 0x0008

            flags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE | JOB_OBJECT_LIMIT_DIE_ON_UNHANDLED_EXCEPTION
            if max_memory_mb > 0:
                flags |= JOB_OBJECT_LIMIT_PROCESS_MEMORY | JOB_OBJECT_LIMIT_JOB_MEMORY
                jeli.ProcessMemoryLimit = mem_bytes
                jeli.JobMemoryLimit = mem_bytes

            if max_processes > 0:
                flags |= JOB_OBJECT_LIMIT_ACTIVE_PROCESS
                jeli.BasicLimitInformation.ActiveProcessLimit = max_processes

            jeli.BasicLimitInformation.LimitFlags = flags
            JobObjectExtendedLimitInformation = 9
            kernel32.SetInformationJobObject(
                h_job,
                JobObjectExtendedLimitInformation,
                ctypes.byref(jeli),
                ctypes.sizeof(jeli),
            )

            # CPU Rate Control
            if 0 < cpu_rate_percent <= 100:
                cpu_info = _JOBOBJECT_CPU_RATE_CONTROL_INFORMATION()
                cpu_info.ControlFlags = 0x1 | 0x4  # ENABLE | HARD_CAP
                cpu_info.CpuRate = cpu_rate_percent * 100
                JobObjectCpuRateControlInformation = 15
                kernel32.SetInformationJobObject(
                    h_job,
                    JobObjectCpuRateControlInformation,
                    ctypes.byref(cpu_info),
                    ctypes.sizeof(cpu_info),
                )

            return NativeSandboxEnclave(self, h_job, mem_bytes, is_direct_win32=True)
        except Exception as exc:
            logger.debug("Failed to create Win32 Job Object sandbox: %s", exc)
            return None

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
                return NativeSandboxEnclave(self, handle, mem_bytes, is_direct_win32=False)

        if os.name == "nt":
            return self._create_win32_job_enclave(max_memory_mb, max_processes, cpu_rate_percent)

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
