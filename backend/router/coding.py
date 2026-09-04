"""
Sovereign AI Workbench — Coding Module

Specialized support for code generation with Qwen2.5-Coder-7B.

Provides:
- Coding-specific system prompts
- Code block extraction from markdown LLM output
- Structured CodeBlock / CodeGenerationResult types
- High-level generate_code() function

This is the foundation for the Phase 10 sandbox loop:
    generate → execute → observe → fix → re-execute

Usage:
    from backend.router.coding import extract_code_blocks, CODING_SYSTEM_PROMPT

    blocks = extract_code_blocks(model_output)
    for block in blocks:
        print(f"{block.language}: {len(block.code)} chars")
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger("sovereign.coding")


# ── System Prompts ────────────────────────────────────────────────────────────

CODING_SYSTEM_PROMPT = """\
You are a Sovereign AI coding assistant running entirely on local hardware.
You specialize in writing clean, production-quality Python code.

Rules:
1. Write complete, executable code — no pseudocode or placeholders.
2. Include proper error handling with try/except blocks.
3. Add type hints to all function signatures.
4. Include concise docstrings for functions and classes.
5. Use standard library modules when possible; minimize external dependencies.
6. Always wrap main logic in an `if __name__ == "__main__":` block when appropriate.
7. Format output as a single markdown code block with the language specified.
8. If the task requires reading files, accept file paths as function parameters.
9. Print results to stdout so they can be captured by the execution sandbox.
10. Never access the network, external APIs, or cloud services.

When generating data analysis code:
- Use pandas for tabular data processing.
- Print summary statistics and key findings to stdout.
- Save output files (CSV, XLSX) when the user requests persistent results.

When generating utility code:
- Make functions reusable and composable.
- Include example usage in the __main__ block."""

CODING_SYSTEM_PROMPT_MINIMAL = """\
You are a code generation assistant. Write clean, executable Python code.
Include error handling and type hints. Format as a markdown code block.
Never access external networks or APIs."""

DATA_ANALYSIS_SYSTEM_PROMPT = """\
You are a Sovereign AI data analysis assistant running on local hardware.
You write Python code for data processing, statistical analysis, and reporting.

Rules:
1. Use pandas for reading and processing tabular data (CSV, XLSX).
2. Use proper statistical methods — avoid guessing or approximating.
3. Print clear summary tables and key findings to stdout.
4. Handle missing data, type errors, and edge cases gracefully.
5. When creating charts, use matplotlib and save to files (don't plt.show()).
6. Accept input file paths as command-line arguments or function parameters.
7. Never access external networks, APIs, or cloud services.

Output format:
- Wrap code in a ```python markdown block.
- Include brief comments explaining the analysis approach."""


# ── Data Types ────────────────────────────────────────────────────────────────


@dataclass
class CodeBlock:
    """A single extracted code block from LLM output."""
    language: str
    code: str
    description: str = ""
    line_count: int = 0

    def __post_init__(self):
        self.line_count = len(self.code.strip().splitlines()) if self.code else 0


@dataclass
class CodeGenerationResult:
    """
    Structured result from a code generation request.

    Contains extracted code blocks, the raw model response,
    and metadata about the generation.
    """
    code_blocks: list[CodeBlock] = field(default_factory=list)
    raw_response: str = ""
    model_used: str = ""
    language: str = "python"
    duration_ms: float = 0.0
    success: bool = False
    error: Optional[str] = None

    @property
    def primary_code(self) -> str:
        """Return the first code block's content, or empty string."""
        if self.code_blocks:
            return self.code_blocks[0].code
        return ""

    @property
    def total_lines(self) -> int:
        """Total lines across all code blocks."""
        return sum(b.line_count for b in self.code_blocks)

    def to_dict(self) -> dict:
        """Serialize for API response."""
        return {
            "code_blocks": [
                {
                    "language": b.language,
                    "code": b.code,
                    "description": b.description,
                    "line_count": b.line_count,
                }
                for b in self.code_blocks
            ],
            "raw_response": self.raw_response,
            "model_used": self.model_used,
            "language": self.language,
            "duration_ms": self.duration_ms,
            "success": self.success,
            "error": self.error,
            "total_lines": self.total_lines,
        }


# ── Code Block Extraction ─────────────────────────────────────────────────────

# Regex: matches ```lang\n...code...\n```
# Handles optional language specifier and nested content
_CODE_BLOCK_PATTERN = re.compile(
    r"```(\w*)\s*\n(.*?)```",
    re.DOTALL,
)


def extract_code_blocks(text: str) -> list[CodeBlock]:
    """
    Extract fenced code blocks from markdown-formatted LLM output.

    Handles:
    - ```python\\ncode\\n```
    - ```\\ncode\\n``` (no language specified)
    - Multiple code blocks in one response
    - Strips leading/trailing whitespace from code

    Args:
        text: Raw LLM response text

    Returns:
        List of CodeBlock objects, ordered by appearance
    """
    if not text:
        return []

    blocks: list[CodeBlock] = []

    for match in _CODE_BLOCK_PATTERN.finditer(text):
        language = match.group(1).strip().lower() or "text"
        code = match.group(2).strip()

        if not code:
            continue

        # Try to extract a description from text before the code block
        block_start = match.start()
        preceding_text = text[:block_start].strip()
        description = ""
        if preceding_text:
            # Take the last non-empty line before the code block as description
            lines = preceding_text.split("\n")
            for line in reversed(lines):
                line = line.strip()
                if line and not line.startswith("```"):
                    # Clean markdown formatting
                    description = line.lstrip("#").lstrip("*").lstrip("-").strip()
                    # Truncate long descriptions
                    if len(description) > 200:
                        description = description[:197] + "..."
                    break

        blocks.append(CodeBlock(
            language=language,
            code=code,
            description=description,
        ))

    return blocks


def extract_primary_code(text: str, preferred_language: str = "python") -> str:
    """
    Extract the most relevant code block from LLM output.

    Priority:
    1. First block matching the preferred language
    2. First block of any language
    3. Empty string if no blocks found

    Args:
        text: Raw LLM response text
        preferred_language: Language to prefer (default: "python")

    Returns:
        Code string, or empty string if no code found
    """
    blocks = extract_code_blocks(text)
    if not blocks:
        return ""

    # Prefer the requested language
    for block in blocks:
        if block.language == preferred_language:
            return block.code

    # Fall back to first block
    return blocks[0].code


def get_system_prompt(task_type: str = "coding") -> str:
    """
    Get the appropriate system prompt for a coding task.

    Args:
        task_type: "coding" or "data_analysis"

    Returns:
        System prompt string
    """
    if task_type == "data_analysis":
        return DATA_ANALYSIS_SYSTEM_PROMPT
    return CODING_SYSTEM_PROMPT
