"""
Sovereign AI Workbench — Coder Service Bridge

Provides a slim generate_code() function used by the coding agent's planner
and repair loop.  Delegates to the primary model router so that every code
generation request participates in VRAM discipline, GPU scheduling, and
telemetry.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger("sovereign.coder_service")


class CoderServiceError(RuntimeError):
    """Raised when code generation fails."""
    pass


@dataclass
class CodeGenerationResult:
    """Minimal result returned to callers (planner, repair loop)."""
    code: str


async def generate_code(
    task_description: str,
    prior_code: Optional[str] = None,
    error_output: Optional[str] = None,
) -> CodeGenerationResult:
    """
    Generate or repair Python code via the primary model router.

    The router handles model loading, VRAM management, and Ollama
    communication.  This function adds repair context when supplied
    and extracts the first code block from the model response.
    """
    # Lazy import to avoid circular imports at module load time.
    from backend.router.router import model_router

    context = ""
    if prior_code or error_output:
        context = "You are repairing broken code.\n"
        if prior_code:
            context += f"Prior Code:\n```python\n{prior_code}\n```\n"
        if error_output:
            context += f"Error Output:\n```text\n{error_output}\n```\n"

    prompt = f"{context}\n\nTask: {task_description}" if context else task_description

    try:
        result = await model_router.generate_code(
            prompt=prompt,
            language="python",
            temperature=0.3,
            max_tokens=4096,
        )

        if not result.success:
            raise CoderServiceError(
                result.error or "Code generation returned no code blocks."
            )

        code = result.primary_code
        if not code:
            raise CoderServiceError(
                "Model responded but no executable code block was extracted."
            )

        return CodeGenerationResult(code=code)

    except CoderServiceError:
        raise
    except Exception as e:
        raise CoderServiceError(f"Model generation failed: {e}") from e
