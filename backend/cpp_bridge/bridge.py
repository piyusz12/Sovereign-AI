"""
Sovereign AI Workbench — C++ Fast Core Bridge (ctypes)

Connects Python orchestration to the compiled C++ sovereign_core.dll
for sub-millisecond routing, VRAM safety gates, and firewall evaluation.
Provides seamless high-speed native Python fallback when running outside
a 64-bit compiled shared library environment.
"""

from __future__ import annotations

import ctypes
import logging
import os
from pathlib import Path
from typing import Optional, Tuple

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

            self._dll.sovereign_core_init.restype = ctypes.c_int
            self._dll.sovereign_core_init.argtypes = []

            self._dll.sovereign_router_classify.restype = ctypes.c_int
            self._dll.sovereign_router_classify.argtypes = [
                ctypes.c_char_p,
                ctypes.c_int,
                ctypes.POINTER(ctypes.c_int),
                ctypes.c_char_p,
                ctypes.c_int,
                ctypes.POINTER(ctypes.c_float),
            ]

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

            self._dll.sovereign_firewall_evaluate.restype = ctypes.c_int
            self._dll.sovereign_firewall_evaluate.argtypes = [
                ctypes.c_char_p,
                ctypes.c_char_p,
                ctypes.POINTER(ctypes.c_int),
                ctypes.c_char_p,
                ctypes.c_int,
            ]

            self._dll.sovereign_prompt_estimate_tokens.restype = ctypes.c_size_t
            self._dll.sovereign_prompt_estimate_tokens.argtypes = [ctypes.c_char_p]

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

    def memory_prepare_switch(self, target_model_id: str, required_vram_mb: int = 5500) -> Tuple[bool, str]:
        """
        Check VRAM safety and get evicted model name.
        """
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

        # Python Fast Path Fallback (Enforce Priority 2: Single heavy model active on RTX 4060)
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

    def firewall_evaluate(self, action: str, user_role: str = "engineering") -> Tuple[str, str, bool]:
        """
        Fast action firewall check.
        Returns (decision_policy, reason, sovereign_compliant).
        """
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

        # Python Fast Path Fallback
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
