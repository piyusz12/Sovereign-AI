"""
Tests — Vision Module

Verifies system prompts and formatting for Qwen3-VL-8B integration.
"""

import pytest
from backend.router.vision import (
    VisionResult,
    get_system_prompt,
    VISION_SYSTEM_PROMPT,
    VISION_JSON_PROMPT,
)


def test_get_system_prompt():
    """Verify system prompts are retrieved correctly based on the structured flag."""
    assert get_system_prompt(structured=False) == VISION_SYSTEM_PROMPT
    assert get_system_prompt(structured=True) == VISION_JSON_PROMPT


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
