"""
Tests — Vision Module

Verifies system prompts, error handling, input validation, and formatting
for the Qwen3-VL-8B vision integration.
"""

import base64
import io
import pytest

from PIL import Image

from backend.router.vision import (
    VisionResult,
    get_system_prompt,
    VISION_SYSTEM_PROMPT,
    VISION_JSON_PROMPT,
    _validate_base64_image,
    _compress_image,
)


# ── System Prompt Tests ───────────────────────────────────────────────────────


def test_get_system_prompt():
    """Verify system prompts are retrieved correctly based on the structured flag."""
    assert get_system_prompt(structured=False) == VISION_SYSTEM_PROMPT
    assert get_system_prompt(structured=True) == VISION_JSON_PROMPT


# ── VisionResult Tests ────────────────────────────────────────────────────────


def test_vision_result_serialization():
    """Verify VisionResult can be serialized to a dictionary."""
    result = VisionResult(
        content="The image shows a P&ID diagram.",
        model_used="qwen3-vl:8b",
        duration_ms=450.5,
        success=True,
    )
    d = result.to_dict()
    assert d["content"] == "The image shows a P&ID diagram."
    assert d["model_used"] == "qwen3-vl:8b"
    assert d["duration_ms"] == 450.5
    assert d["success"] is True
    assert d["error"] is None

    result_error = VisionResult(
        content="",
        success=False,
        error="Failed to connect to provider",
    )
    d_error = result_error.to_dict()
    assert d_error["success"] is False
    assert d_error["error"] == "Failed to connect to provider"


def test_vision_result_error_state_defaults():
    """Verify VisionResult error states have correct default values."""
    result = VisionResult(content="", success=False, error="Some error")
    assert result.model_used == ""
    assert result.duration_ms == 0.0
    d = result.to_dict()
    assert d["content"] == ""
    assert d["model_used"] == ""


# ── Input Validation Tests ────────────────────────────────────────────────────


def _make_test_image_b64(width=100, height=100, color="red", fmt="JPEG") -> str:
    """Create a small valid base64-encoded test image."""
    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def test_validate_base64_image_empty():
    """Empty string should fail validation."""
    is_valid, error = _validate_base64_image("")
    assert not is_valid
    assert "empty" in error.lower()


def test_validate_base64_image_whitespace_only():
    """Whitespace-only string should fail validation."""
    is_valid, error = _validate_base64_image("   \n\t  ")
    assert not is_valid
    assert "empty" in error.lower()


def test_validate_base64_image_invalid_encoding():
    """Non-base64 string should fail validation."""
    is_valid, error = _validate_base64_image("not-valid-base64!!!")
    assert not is_valid
    assert "base64" in error.lower() or "encoding" in error.lower()


def test_validate_base64_image_not_an_image():
    """Valid base64 but not an image should fail validation."""
    text_b64 = base64.b64encode(b"Hello, this is just text.").decode("utf-8")
    is_valid, error = _validate_base64_image(text_b64)
    assert not is_valid
    assert "not a valid image" in error.lower()


def test_validate_base64_image_valid():
    """A proper JPEG image should pass validation."""
    b64 = _make_test_image_b64()
    is_valid, error = _validate_base64_image(b64)
    assert is_valid
    assert error == ""


# ── Compression Tests ─────────────────────────────────────────────────────────


def test_compress_image_large():
    """Large images should be resized to fit within 1024x1024."""
    b64 = _make_test_image_b64(width=2000, height=3000)
    compressed_b64 = _compress_image(b64)

    compressed_bytes = base64.b64decode(compressed_b64)
    img = Image.open(io.BytesIO(compressed_bytes))
    assert img.size[0] <= 1024
    assert img.size[1] <= 1024


def test_compress_image_small():
    """Small images should pass through without error."""
    b64 = _make_test_image_b64(width=64, height=64)
    compressed_b64 = _compress_image(b64)
    assert compressed_b64  # Should return something non-empty


def test_compress_image_corrupt_data():
    """Corrupt base64 data should raise ValueError, not silently return garbage."""
    with pytest.raises(ValueError, match="Cannot decode"):
        _compress_image("not-valid-base64!!!")


def test_compress_image_valid_base64_but_not_image():
    """Valid base64 but not image data should raise ValueError."""
    text_b64 = base64.b64encode(b"Just some text content").decode("utf-8")
    with pytest.raises(ValueError, match="Cannot open"):
        _compress_image(text_b64)


def test_compress_image_png_converted_to_jpeg():
    """PNG images should be converted to JPEG format."""
    b64 = _make_test_image_b64(fmt="PNG")
    compressed_b64 = _compress_image(b64)
    compressed_bytes = base64.b64decode(compressed_b64)
    img = Image.open(io.BytesIO(compressed_bytes))
    assert img.format == "JPEG"


# ── analyze_vision Tests ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_analyze_vision_empty_prompt():
    """Empty prompt should return a failed VisionResult."""
    from backend.router.vision import analyze_vision

    result = await analyze_vision(prompt="", image_base64=_make_test_image_b64())
    assert not result.success
    assert "empty" in result.error.lower()


@pytest.mark.asyncio
async def test_analyze_vision_empty_image():
    """Empty image_base64 should return a failed VisionResult."""
    from backend.router.vision import analyze_vision

    result = await analyze_vision(prompt="Describe this image", image_base64="")
    assert not result.success
    assert "empty" in result.error.lower()


@pytest.mark.asyncio
async def test_analyze_vision_invalid_base64():
    """Invalid base64 should return a failed VisionResult, not crash."""
    from backend.router.vision import analyze_vision

    result = await analyze_vision(prompt="Describe this", image_base64="!!!invalid!!!")
    assert not result.success
    assert result.error  # Should have a meaningful error message
