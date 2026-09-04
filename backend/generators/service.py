"""
Sovereign AI Workbench — Deliverable Service

Unified router/wrapper for deliverable generation and validation.
Returns tuple of (filepath, error) so tools can trigger repair loops.
"""

import logging
import os
from typing import Tuple

from backend.generators.docx_generator import docx_generator
from backend.generators.xlsx_generator import xlsx_generator
from backend.generators.pptx_generator import pptx_generator
from backend.generators.code_generator import code_generator
from backend.generators.validator import validator

logger = logging.getLogger("sovereign.generators.service")

class DeliverableService:
    """Wraps generation and validation for deliverables."""

    async def create_and_validate_docx(
        self, title: str, content: dict, template: str = "default"
    ) -> Tuple[str, str]:
        """Generate DOCX and validate it."""
        try:
            if template == "approval_note":
                filepath = await docx_generator.generate_approval_note(
                    title=title,
                    inspection_data=content.get("inspection_data", {}),
                    analysis=content.get("analysis", ""),
                    recommendation=content.get("recommendation", ""),
                    sources=content.get("sources", []),
                )
            else:
                filepath = await docx_generator.generate_report(
                    title=title,
                    sections=content.get("sections", []),
                )
                
            if not filepath or not os.path.exists(filepath):
                return "", "Failed to generate DOCX."
                
            val = validator.validate_docx(filepath)
            if not val.is_valid:
                return "", f"Validation failed: {val.error}"
                
            return filepath, ""
        except Exception as e:
            return "", str(e)

    async def create_and_validate_xlsx(
        self, title: str, data: list[dict], summary: dict = None
    ) -> Tuple[str, str]:
        """Generate XLSX and validate it."""
        try:
            filepath = await xlsx_generator.generate_analysis_report(title=title, data=data, summary=summary)
            if not filepath or not os.path.exists(filepath):
                return "", "Failed to generate XLSX."
                
            val = validator.validate_xlsx(filepath)
            if not val.is_valid:
                return "", f"Validation failed: {val.error}"
                
            return filepath, ""
        except Exception as e:
            return "", str(e)

    async def create_and_validate_pptx(
        self, title: str, slides: list[dict]
    ) -> Tuple[str, str]:
        """Generate PPTX and validate it."""
        try:
            filepath = await pptx_generator.generate_presentation(title=title, slides=slides)
            if not filepath or not os.path.exists(filepath):
                return "", "Failed to generate PPTX."
                
            val = validator.validate_pptx(filepath)
            if not val.is_valid:
                return "", f"Validation failed: {val.error}"
                
            return filepath, ""
        except Exception as e:
            return "", str(e)

    async def create_and_validate_code_package(
        self, title: str, files: dict[str, str], required_files: list[str] = None
    ) -> Tuple[str, str]:
        """Generate Code Package ZIP and validate it."""
        try:
            filepath = await code_generator.generate_code_package(title=title, files=files)
            if not filepath or not os.path.exists(filepath):
                return "", "Failed to generate ZIP package."
                
            val = validator.validate_code_package(filepath, required_files)
            if not val.is_valid:
                return "", f"Validation failed: {val.error}"
                
            return filepath, ""
        except Exception as e:
            return "", str(e)

# Global instance
deliverable_service = DeliverableService()
