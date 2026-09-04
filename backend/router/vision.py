"""
Sovereign AI Workbench — Vision Module

Specialized support for multimodal tasks with Qwen3-VL-8B.
Handles system prompts and structural formatting for image analysis tasks.
"""

from __future__ import annotations

import base64
import io
import logging
import time
from dataclasses import dataclass
from typing import Optional

from PIL import Image

from backend.settings import settings
from backend.router.ollama_client import ollama_client

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


def _compress_image(image_base64: str) -> str:
    try:
        image_bytes = base64.b64decode(image_base64)
        img = Image.open(io.BytesIO(image_bytes))
        
        # Resize if larger than 1024 on any side
        max_size = (1024, 1024)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        if img.mode != 'RGB':
            img = img.convert('RGB')
            
        out = io.BytesIO()
        img.save(out, format="JPEG", quality=85)
        return base64.b64encode(out.getvalue()).decode("utf-8")
    except Exception as e:
        logger.warning(f"Image compression failed, using original: {e}")
        return image_base64


async def analyze_vision(prompt: str, image_base64: str, structured: bool = False) -> VisionResult:
    """
    Execute a vision task using Qwen3-VL-8B via Ollama.
    """
    start_time = time.time()
    try:
        image_base64 = _compress_image(image_base64)
        messages = [
            {"role": "system", "content": get_system_prompt(structured=structured)},
            {"role": "user", "content": prompt, "images": [image_base64]}
        ]
        
        response = await ollama_client.chat(
            model=settings.ollama_vision_model,
            messages=messages,
            temperature=0.1,
            max_tokens=1024,
        )
        duration = round((time.time() - start_time) * 1000, 2)
        
        return VisionResult(
            content=response.content,
            model_used=response.model,
            duration_ms=duration,
            success=True
        )
    except Exception as e:
        logger.error(f"Vision analysis failed: {e}")
        return VisionResult(
            content="",
            success=False,
            error=str(e),
            duration_ms=round((time.time() - start_time) * 1000, 2)
        )
