"""
Sovereign AI Workbench — Vision Module

Specialized support for multimodal tasks with Qwen3-VL-8B.
Handles system prompts and structural formatting for image analysis tasks.

The module ensures that vision inference participates in the model
registry's single-GPU discipline — another heavy model is unloaded
before the vision model is loaded into VRAM.
"""

from __future__ import annotations

import asyncio
import base64
import binascii
import io
import logging
import re
import time
from dataclasses import dataclass
from typing import Optional

from PIL import Image

from backend.settings import settings

logger = logging.getLogger("sovereign.vision")

# ── Constants ─────────────────────────────────────────────────────────────────

MAX_IMAGE_BYTES = 20 * 1024 * 1024  # 20 MB max raw image size
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 1.0


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


def clean_base64_image(image_data: str) -> str:
    """
    Clean and normalize a base64 image string.
    Strips data URI prefixes (e.g. 'data:image/png;base64,') and whitespace.
    """
    if not image_data:
        return ""
    data = image_data.strip()
    if data.startswith("data:"):
        if "," in data:
            data = data.split(",", 1)[1].strip()
    return re.sub(r"\s+", "", data)


def _validate_base64_image(image_base64: str) -> tuple[bool, str]:
    """
    Validate that image_base64 is non-empty, valid base64, and within size limits.
    Returns (is_valid, error_message).
    """
    if not image_base64 or not image_base64.strip():
        return False, "Image data is empty."

    raw_str = image_base64.strip()
    if raw_str.startswith("<svg") or "<svg" in raw_str[:120].lower():
        return False, "SVG vector images cannot be directly processed by vision models. Please upload a PNG or JPEG raster image."

    cleaned = clean_base64_image(image_base64)
    if not cleaned:
        return False, "Image data is empty."

    try:
        raw_bytes = base64.b64decode(cleaned, validate=True)
    except (binascii.Error, ValueError) as e:
        return False, f"Invalid base64 encoding: {e}"

    if len(raw_bytes) > MAX_IMAGE_BYTES:
        size_mb = round(len(raw_bytes) / (1024 * 1024), 1)
        return False, f"Image too large ({size_mb} MB). Maximum is {MAX_IMAGE_BYTES // (1024 * 1024)} MB."

    # Verify it's actually a decodable image
    try:
        img = Image.open(io.BytesIO(raw_bytes))
        img.verify()  # Verify but don't fully load
    except Exception as e:
        return False, f"Data is not a valid image: {e}"

    return True, ""


def _compress_image(image_base64: str) -> str:
    """
    Compress and resize an image for vision model input.
    Strips data URI prefixes, resizes to max 1024x1024, and re-encodes as clean JPEG.
    Raises ValueError for corrupt/undecodable images.
    """
    cleaned = clean_base64_image(image_base64)
    try:
        image_bytes = base64.b64decode(cleaned)
    except (binascii.Error, ValueError) as e:
        raise ValueError(f"Cannot decode base64 image data: {e}")

    try:
        img = Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        raise ValueError(f"Cannot open image data (corrupt or unsupported format): {e}")

    try:
        # Resize if larger than 1024 on any side
        max_size = (1024, 1024)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)

        if img.mode != 'RGB':
            img = img.convert('RGB')

        out = io.BytesIO()
        img.save(out, format="JPEG", quality=85)
        return base64.b64encode(out.getvalue()).decode("utf-8")
    except Exception as e:
        # Image is valid but resize/convert failed — return cleaned base64
        logger.warning("Image resize failed, using cleaned original (%s): %s", getattr(img, 'size', 'unknown'), e)
        return cleaned


async def _ensure_vision_model_loaded() -> str:
    """
    Ensure the vision model is loaded in VRAM through the model registry,
    which handles unloading other heavy models as needed.

    Returns the actual model_id to use for inference.
    """
    from backend.router.model_registry import model_registry
    from backend.router.ollama_client import ollama_client

    # Attempt dynamic detection to use whichever vision model is installed
    try:
        resolved = await ollama_client.resolve_model_name("vision")
        if resolved:
            return resolved
    except Exception as resolve_err:
        logger.debug("Ollama vision model auto-resolution skipped: %s", resolve_err)

    try:
        model_config = await model_registry.load_model("vision")
        return model_config.model_id
    except Exception as e:
        logger.warning(
            "Failed to load vision model via registry (%s), "
            "falling back to settings.ollama_vision_model",
            e,
        )
        return settings.ollama_vision_model


async def analyze_vision(prompt: str, image_base64: str, structured: bool = False) -> VisionResult:
    """
    Execute a vision task using Qwen3-VL-8B via Ollama.

    Validates input, compresses the image, ensures the model is loaded
    (with VRAM discipline), and retries on transient errors.
    """
    from backend.router.ollama_client import ollama_client

    start_time = time.time()

    # ── Input Validation ──────────────────────────────────────────────────
    if not prompt or not prompt.strip():
        return VisionResult(
            content="",
            success=False,
            error="Prompt cannot be empty.",
            duration_ms=0.0,
        )

    is_valid, validation_error = _validate_base64_image(image_base64)
    if not is_valid:
        return VisionResult(
            content="",
            success=False,
            error=validation_error,
            duration_ms=round((time.time() - start_time) * 1000, 2),
        )

    # ── Compression ───────────────────────────────────────────────────────
    try:
        image_base64 = _compress_image(image_base64)
    except ValueError as e:
        return VisionResult(
            content="",
            success=False,
            error=str(e),
            duration_ms=round((time.time() - start_time) * 1000, 2),
        )

    # ── Load vision model (VRAM discipline) ───────────────────────────────
    vision_model_id = await _ensure_vision_model_loaded()

    # ── Inference with Retry ──────────────────────────────────────────────
    messages = [
        {"role": "system", "content": get_system_prompt(structured=structured)},
        {"role": "user", "content": prompt, "images": [image_base64]}
    ]

    last_error: Optional[Exception] = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = await ollama_client.chat(
                model=vision_model_id,
                messages=messages,
                temperature=0.1,
                max_tokens=1024,
            )
            duration = round((time.time() - start_time) * 1000, 2)

            # Detect empty / whitespace-only responses
            if not response.content or not response.content.strip():
                logger.warning("Vision model returned empty response (attempt %d/%d)", attempt, MAX_RETRIES)
                last_error = RuntimeError("Vision model returned an empty response.")
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(RETRY_BACKOFF_SECONDS * attempt)
                    continue
                return VisionResult(
                    content="",
                    model_used=response.model,
                    duration_ms=duration,
                    success=False,
                    error="Vision model returned an empty response after retries.",
                )

            return VisionResult(
                content=response.content,
                model_used=response.model,
                duration_ms=duration,
                success=True,
            )

        except (ConnectionError, OSError) as e:
            # Transient network / Ollama errors — retry
            last_error = e
            logger.warning("Vision inference transient error (attempt %d/%d): %s", attempt, MAX_RETRIES, e)
            if attempt < MAX_RETRIES:
                await asyncio.sleep(RETRY_BACKOFF_SECONDS * attempt)
                continue

        except Exception as e:
            # Non-transient errors — fail immediately
            logger.error("Vision analysis failed: %s", e)
            return VisionResult(
                content="",
                success=False,
                error=str(e),
                duration_ms=round((time.time() - start_time) * 1000, 2),
            )

    # All retries exhausted
    return VisionResult(
        content="",
        success=False,
        error=f"Vision analysis failed after {MAX_RETRIES} attempts: {last_error}",
        duration_ms=round((time.time() - start_time) * 1000, 2),
    )
