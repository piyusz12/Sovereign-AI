"""
Sovereign AI Workbench — Vision Module

Specialized support for multimodal tasks with Qwen3-VL-8B.
Handles system prompts and structural formatting for image analysis tasks.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger("sovereign.vision")


# ── System Prompts ────────────────────────────────────────────────────────────

VISION_SYSTEM_PROMPT = """\
You are a Sovereign AI vision assistant operating on local hardware.
You analyze images, engineering diagrams, P&IDs, scanned documents, and technical drawings.

Rules:
1. Describe what you see precisely.
2. Identify labeled components, measurements, and annotations.
3. When identifying equipment in a P&ID or schematic, extract the equipment tags (e.g., V-204, P-101).
4. Do not hallucinate details that are not visible in the image.
5. If text is illegible, state that clearly.
6. Never reference or attempt to access external services or APIs."""

VISION_JSON_PROMPT = """\
You are a Sovereign AI vision assistant operating on local hardware.
You analyze images, engineering diagrams, P&IDs, scanned documents, and technical drawings.

Rules:
1. Describe what you see precisely.
2. Identify labeled components, measurements, and annotations.
3. When identifying equipment in a P&ID or schematic, extract the equipment tags (e.g., V-204, P-101).
4. Do not hallucinate details that are not visible in the image.
5. Return your findings as a structured JSON object with keys like "description", "equipment_tags", and "text_found".
6. Never reference or attempt to access external services or APIs."""


# ── Data Types ────────────────────────────────────────────────────────────────

@dataclass
class VisionResult:
    """Structured result from a vision analysis request."""
    content: str
    model_used: str = ""
    duration_ms: float = 0.0
    success: bool = False
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """Serialize for API response."""
        return {
            "content": self.content,
            "model_used": self.model_used,
            "duration_ms": self.duration_ms,
            "success": self.success,
            "error": self.error,
        }


def get_system_prompt(task_type: str = "vision", structured: bool = False) -> str:
    """
    Get the appropriate system prompt for a vision task.
    """
    if structured:
        return VISION_JSON_PROMPT
    return VISION_SYSTEM_PROMPT
