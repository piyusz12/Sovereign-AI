"""
Sovereign AI Workbench — Coder Service Bridge

Bridges the standalone synchronous/async repair loop with the asynchronous
ModelRouter built in Phase 7.
"""

from __future__ import annotations

from typing import Optional
from dataclasses import dataclass

from backend.router.router import model_router


class CoderServiceError(RuntimeError):
    """Raised when code generation fails."""
    pass


@dataclass
class CodeGenerationResult:
    code: str


async def generate_code(
    task_description: str,
    prior_code: Optional[str] = None,
    error_output: Optional[str] = None,
) -> CodeGenerationResult:
    """
    Generate or repair Python code using the router's coding model.
    """
    # Build context if this is a repair attempt
    context = ""
    if prior_code or error_output:
        context = "You are repairing broken code.\n"
        if prior_code:
            context += f"Prior Code:\n```python\n{prior_code}\n```\n"
        if error_output:
            context += f"Error Output:\n```text\n{error_output}\n```\n"

    try:
        # Call the actual async router
        result = await model_router.generate_code(
            prompt=task_description,
            language="python",
            context=context if context else None,
            temperature=0.3,
        )

        if not result.success or not result.code_blocks:
            raise CoderServiceError(
                result.error or "Failed to generate valid code blocks."
            )

        # Return the first code block (the most relevant one)
        return CodeGenerationResult(code=result.code_blocks[0].code)

    except Exception as e:
        if isinstance(e, CoderServiceError):
            raise
        raise CoderServiceError(f"Model generation failed: {e}")
