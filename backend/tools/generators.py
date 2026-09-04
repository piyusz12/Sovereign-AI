"""
Sovereign AI Workbench — Document Generator Tools

Generate DOCX, XLSX, PPTX from AI analysis.
These are the tool wrappers; actual generation logic is in backend/generators/.
"""

from __future__ import annotations

from typing import Any
from pathlib import Path

from backend.tools.base import BaseTool, ToolPermission
from backend.generators.service import deliverable_service


class CreateDocxTool(BaseTool):
    """Generate a DOCX document from structured data."""

    def __init__(self):
        super().__init__(
            name="create_docx",
            description="Generate a Word document (DOCX) from structured data",
            permission=ToolPermission(
                name="create_docx",
                allowed_roles=["admin", "engineering", "operations"],
            ),
        )

    async def _run(self, title: str, content: dict, template: str = "default", **kwargs) -> Any:
        filepath, error = await deliverable_service.create_and_validate_docx(
            title=title, content=content, template=template
        )
        if error:
            return {"status": "error", "error": error}
            
        return {
            "filename": Path(filepath).name if filepath else f"{title}.docx",
            "filepath": filepath,
            "status": "success",
        }


class CreateXlsxTool(BaseTool):
    """Generate an XLSX spreadsheet from data."""

    def __init__(self):
        super().__init__(
            name="create_xlsx",
            description="Generate an Excel spreadsheet (XLSX) from data",
            permission=ToolPermission(
                name="create_xlsx",
                allowed_roles=["admin", "engineering", "finance", "operations"],
            ),
        )

    async def _run(self, title: str, data: list[dict], **kwargs) -> Any:
        filepath, error = await deliverable_service.create_and_validate_xlsx(
            title=title, data=data
        )
        if error:
            return {"status": "error", "error": error}
            
        return {
            "filename": Path(filepath).name if filepath else f"{title}.xlsx",
            "filepath": filepath,
            "status": "success",
        }


class CreatePptxTool(BaseTool):
    """Generate a PPTX presentation from structured slides."""

    def __init__(self):
        super().__init__(
            name="create_pptx",
            description="Generate a PowerPoint presentation (PPTX) from structured data",
            permission=ToolPermission(
                name="create_pptx",
                allowed_roles=["admin", "engineering", "operations"],
            ),
        )

    async def _run(self, title: str, slides: list[dict], **kwargs) -> Any:
        filepath, error = await deliverable_service.create_and_validate_pptx(
            title=title, slides=slides
        )
        if error:
            return {"status": "error", "error": error}
            
        return {
            "filename": Path(filepath).name if filepath else f"{title}.pptx",
            "filepath": filepath,
            "status": "success",
        }

class CreateCodePackageTool(BaseTool):
    """Generate a ZIP code package."""

    def __init__(self):
        super().__init__(
            name="create_code_package",
            description="Generate a ZIP code package from working scripts",
            permission=ToolPermission(
                name="create_code_package",
                allowed_roles=["admin", "engineering"],
            ),
        )

    async def _run(self, title: str, files: dict[str, str], **kwargs) -> Any:
        filepath, error = await deliverable_service.create_and_validate_code_package(
            title=title, files=files
        )
        if error:
            return {"status": "error", "error": error}
            
        return {
            "filename": Path(filepath).name if filepath else f"{title}.zip",
            "filepath": filepath,
            "status": "success",
        }
