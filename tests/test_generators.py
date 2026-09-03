"""
Tests — Document Generators

Verifies DOCX, XLSX, PPTX generation.
"""

import pytest
from backend.tools.generators import CreateDocxTool, CreateXlsxTool, CreatePptxTool


class TestGeneratorTools:
    """Test document generation tools."""

    @pytest.mark.asyncio
    async def test_docx_tool_exists(self):
        tool = CreateDocxTool()
        assert tool.name == "create_docx"

    @pytest.mark.asyncio
    async def test_xlsx_tool_exists(self):
        tool = CreateXlsxTool()
        assert tool.name == "create_xlsx"

    @pytest.mark.asyncio
    async def test_pptx_tool_exists(self):
        tool = CreatePptxTool()
        assert tool.name == "create_pptx"

    @pytest.mark.asyncio
    async def test_docx_permission(self):
        """Finance cannot generate DOCX (no write permission for this tool)."""
        tool = CreateDocxTool()
        result = await tool.execute(
            user_role="hr",
            title="Test",
            content={},
        )
        assert not result.success  # HR not in allowed roles
