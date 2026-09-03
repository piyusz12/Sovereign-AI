"""
Sovereign AI Workbench — OCR Service

PaddleOCR integration for scanned document recognition.
OCR handles text extraction; the LLM handles interpretation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger("sovereign.documents.ocr")


@dataclass
class OCRResult:
    """Result from OCR processing."""
    text: str
    bounding_boxes: list[dict]
    confidence: float
    page_number: int


class PaddleOCRService:
    """
    OCR service using PaddleOCR.
    Supports CUDA acceleration via container deployment.

    Flow: Scanned PDF → Page images → PaddleOCR → Text + bounding boxes
    """

    def __init__(self):
        self._engine = None

    def _init_engine(self):
        """Lazy-initialize PaddleOCR engine."""
        if self._engine is not None:
            return
        try:
            from paddleocr import PaddleOCR
            self._engine = PaddleOCR(use_angle_cls=True, lang="en", use_gpu=True)
            logger.info("PaddleOCR engine initialized with GPU")
        except ImportError:
            logger.warning("PaddleOCR not installed. Install with: pip install paddleocr")
        except Exception as e:
            logger.error("PaddleOCR init failed: %s", e)

    async def process_image(self, image_path: str, page_number: int = 1) -> OCRResult:
        """
        Run OCR on a single image.

        Args:
            image_path: Path to the image file
            page_number: Page number in the source document

        Returns:
            OCRResult with extracted text and bounding boxes
        """
        self._init_engine()

        if self._engine is None:
            return OCRResult(
                text="[PaddleOCR not available]",
                bounding_boxes=[],
                confidence=0.0,
                page_number=page_number,
            )

        try:
            result = self._engine.ocr(image_path, cls=True)
            texts = []
            boxes = []

            if result and result[0]:
                for line in result[0]:
                    bbox, (text, conf) = line[0], line[1]
                    texts.append(text)
                    boxes.append({
                        "text": text,
                        "confidence": conf,
                        "bbox": bbox,
                    })

            full_text = "\n".join(texts)
            avg_conf = sum(b["confidence"] for b in boxes) / len(boxes) if boxes else 0.0

            return OCRResult(
                text=full_text,
                bounding_boxes=boxes,
                confidence=avg_conf,
                page_number=page_number,
            )
        except Exception as e:
            logger.error("OCR failed on %s: %s", image_path, e)
            return OCRResult(
                text=f"[OCR error: {e}]",
                bounding_boxes=[],
                confidence=0.0,
                page_number=page_number,
            )

    async def process_pdf(self, pdf_path: str) -> list[OCRResult]:
        """Process all pages of a PDF."""
        # TODO Phase 13: Convert PDF pages to images, then OCR each
        logger.info("PDF OCR not yet implemented for: %s", pdf_path)
        return []


# Global instance
ocr_service = PaddleOCRService()
