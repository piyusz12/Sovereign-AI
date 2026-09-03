"""
Sovereign AI Workbench — Document Search Tool

Qdrant-backed document search with RBAC filtering applied BEFORE retrieval.
"""

from __future__ import annotations

from typing import Any, Optional

from backend.tools.base import BaseTool, ToolPermission
from backend.rag.adaptive import adaptive_rag


class DocumentSearchTool(BaseTool):
    """Search the internal knowledge base with RBAC-aware retrieval."""

    def __init__(self):
        super().__init__(
            name="search_documents",
            description="Search internal documents with RBAC-aware hybrid retrieval",
            permission=ToolPermission(
                name="search_documents",
                allowed_roles=["admin", "engineering", "finance", "procurement", "hr", "operations"],
            ),
        )

    async def _run(
        self,
        query: str,
        user_role: str = "engineering",
        department: Optional[str] = None,
        top_k: int = 5,
        **kwargs,
    ) -> Any:
        result = await adaptive_rag.query(
            question=query,
            user_role=user_role,
            department_filter=department,
            top_k=top_k,
        )
        return {
            "answer": result.answer,
            "sources": result.sources,
            "attempts": result.attempts,
            "confidence": result.confidence,
            "status": result.status,
        }
