"""
Sovereign AI Workbench — Filesystem Tools

Sandboxed file operations: read, write, list.
All paths are restricted to the allowed data directories.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from backend.tools.base import BaseTool, ToolPermission

# Allowed directories — the agent can only access these
ALLOWED_DIRS = [
    "./data/documents",
    "./data/processed",
    "./data/output",
]


def _validate_path(file_path: str) -> Path:
    """Validate that a path is within allowed directories."""
    resolved = Path(file_path).resolve()
    for allowed in ALLOWED_DIRS:
        allowed_resolved = Path(allowed).resolve()
        if str(resolved).startswith(str(allowed_resolved)):
            return resolved
    raise PermissionError(f"Path '{file_path}' is outside allowed directories")


class ReadFileTool(BaseTool):
    """Read a file from the allowed data directories."""

    def __init__(self):
        super().__init__(
            name="read_file",
            description="Read the contents of a file from the data directory",
            permission=ToolPermission(
                name="read_file",
                allowed_roles=["admin", "engineering", "finance", "procurement", "hr", "operations"],
            ),
        )

    async def _run(self, file_path: str, **kwargs) -> Any:
        path = _validate_path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        return path.read_text(encoding="utf-8")


class WriteFileTool(BaseTool):
    """Write content to a file in the output directory."""

    def __init__(self):
        super().__init__(
            name="write_file",
            description="Write content to a file in the output directory",
            permission=ToolPermission(
                name="write_file",
                allowed_roles=["admin", "engineering", "operations"],
            ),
        )

    async def _run(self, file_path: str, content: str, **kwargs) -> Any:
        path = _validate_path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return {"written": str(path), "bytes": len(content)}


class ListFilesTool(BaseTool):
    """List files in a data directory."""

    def __init__(self):
        super().__init__(
            name="list_files",
            description="List files in the data directory",
            permission=ToolPermission(
                name="list_files",
                allowed_roles=["admin", "engineering", "finance", "procurement", "hr", "operations"],
            ),
        )

    async def _run(self, directory: str = "./data", **kwargs) -> Any:
        path = _validate_path(directory)
        if not path.is_dir():
            raise NotADirectoryError(f"Not a directory: {directory}")

        files = []
        for item in path.rglob("*"):
            if item.is_file():
                files.append({
                    "path": str(item.relative_to(path)),
                    "size_bytes": item.stat().st_size,
                    "extension": item.suffix,
                })
        return files
