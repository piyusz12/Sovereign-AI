"""
Sovereign AI Workbench — Image Analysis Tool

Uses Qwen3-VL-8B for visual analysis of P&IDs, diagrams, and scanned documents.
"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any, Optional

from backend.tools.base import BaseTool, ToolPermission
from backend.router.vision import analyze_vision


class ImageAnalysisTool(BaseTool):
    """Analyze images using the vision model (Qwen3-VL-8B)."""

    def __init__(self):
        super().__init__(
            name="inspect_image",
            description="Analyze an image using the vision model for P&ID, diagram, or document analysis",
            permission=ToolPermission(
                name="inspect_image",
                allowed_roles=["admin", "engineering", "operations"],
            ),
        )

    async def _run(
        self,
        image_path: Optional[str] = None,
        image_base64: Optional[str] = None,
        prompt: str = "Describe what you see in this image in detail.",
        **kwargs,
    ) -> dict[str, Any]:
        """
        Analyze an image with Qwen3-VL-8B via the Phase 8 analyze_vision pipeline.

        Args:
            image_path: Path to the image file on local disk (optional if image_base64 given)
            image_base64: Raw base64-encoded string (optional if image_path given)
            prompt: Analysis prompt

        Returns:
            Vision model analysis results
        """
        b64_data = image_base64
        if not b64_data:
            if not image_path:
                raise ValueError("Either image_path or image_base64 must be provided.")
            p = Path(image_path)
            if not p.exists() or not p.is_file():
                raise FileNotFoundError(f"Image file not found: {image_path}")
            b64_data = base64.b64encode(p.read_bytes()).decode("utf-8")

        result = await analyze_vision(
            prompt=prompt,
            image_base64=b64_data,
        )

        return {
            "analysis": result.response,
            "image_path": image_path,
            "prompt": prompt,
            "model": result.model_name,
            "metrics": result.metrics,
            "status": "success",
        }
