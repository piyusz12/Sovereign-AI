"""
Sovereign AI Workbench — Python Sandbox Tool

Executes generated Python code inside an isolated Docker container.
Network = disabled, memory/CPU limited, timeout enforced.

This is CRITICAL for the coding-agent demo workflow:
    Generate → Execute → Observe → Error? → Fix → Re-execute → Verify
"""

from __future__ import annotations

import asyncio
import logging
import os
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from backend.tools.base import BaseTool, ToolPermission

logger = logging.getLogger("sovereign.tools.sandbox")

# Sandbox constraints
SANDBOX_IMAGE = os.getenv("SANDBOX_IMAGE", "python:3.12-slim")
SANDBOX_MEMORY = os.getenv("SANDBOX_MEMORY_LIMIT", "512m")
SANDBOX_CPUS = os.getenv("SANDBOX_CPU_LIMIT", "1")
SANDBOX_TIMEOUT = int(os.getenv("SANDBOX_TIMEOUT_SECONDS", "30"))
SANDBOX_NETWORK = "none"  # ALWAYS none — critical for sovereignty


@dataclass
class SandboxResult:
    """Result from sandbox execution."""
    stdout: str
    stderr: str
    exit_code: int
    execution_time_ms: float
    files_created: list[str]
    timed_out: bool = False


class PythonSandboxTool(BaseTool):
    """
    Execute Python code in an isolated Docker container.

    Security guarantees:
    - No network access (--network none)
    - Memory limited (default 512MB)
    - CPU limited (default 1 core)
    - Execution timeout (default 30 seconds)
    - Isolated filesystem
    - No access to host filesystem
    """

    def __init__(self):
        super().__init__(
            name="run_python",
            description="Execute Python code in an isolated Docker sandbox",
            permission=ToolPermission(
                name="run_python",
                allowed_roles=["admin", "engineering"],
                description="Sandboxed Python execution",
            ),
        )

    async def _run(
        self,
        code: str,
        timeout: int = SANDBOX_TIMEOUT,
        input_files: Optional[dict[str, str]] = None,
        **kwargs,
    ) -> Any:
        """
        Execute Python code in a Docker container.

        Args:
            code: Python code to execute
            timeout: Maximum execution time in seconds
            input_files: Dict of filename → content to mount in the container

        Returns:
            SandboxResult with stdout, stderr, exit code
        """
        execution_id = uuid.uuid4().hex[:8]
        workspace_dir = Path(tempfile.mkdtemp(prefix=f"sovereign_sandbox_{execution_id}_"))

        try:
            # Write the Python script
            script_path = workspace_dir / "main.py"
            script_path.write_text(code, encoding="utf-8")

            # Write any input files
            if input_files:
                for filename, content in input_files.items():
                    file_path = workspace_dir / filename
                    file_path.write_text(content, encoding="utf-8")

            # Build Docker command
            docker_cmd = [
                "docker", "run",
                "--rm",
                f"--network={SANDBOX_NETWORK}",
                f"--memory={SANDBOX_MEMORY}",
                f"--cpus={SANDBOX_CPUS}",
                "--read-only",
                "--tmpfs", "/tmp:size=64m",
                "-v", f"{workspace_dir}:/workspace:ro",
                "-w", "/workspace",
                SANDBOX_IMAGE,
                "python", "/workspace/main.py",
            ]

            logger.info("Sandbox [%s]: executing code (%d chars)", execution_id, len(code))

            # Execute with timeout
            process = await asyncio.create_subprocess_exec(
                *docker_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
                timed_out = False
            except asyncio.TimeoutError:
                process.kill()
                stdout_bytes, stderr_bytes = b"", b"Execution timed out"
                timed_out = True

            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")
            exit_code = process.returncode or (-1 if timed_out else 0)

            logger.info(
                "Sandbox [%s]: exit_code=%d, timed_out=%s",
                execution_id, exit_code, timed_out,
            )

            return SandboxResult(
                stdout=stdout,
                stderr=stderr,
                exit_code=exit_code,
                execution_time_ms=0.0,  # TODO: measure actual time
                files_created=[],
                timed_out=timed_out,
            )

        except FileNotFoundError:
            logger.error("Docker not found — is Docker Desktop running?")
            return SandboxResult(
                stdout="",
                stderr="Docker not available. Install Docker Desktop and enable WSL2.",
                exit_code=-1,
                execution_time_ms=0.0,
                files_created=[],
            )
        finally:
            # Cleanup workspace
            import shutil
            shutil.rmtree(workspace_dir, ignore_errors=True)
