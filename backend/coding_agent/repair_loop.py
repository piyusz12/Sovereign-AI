"""
Sovereign AI Workbench — Coding Agent Repair Loop

Generates SEARCH/REPLACE patches and applies them to files.
Uses the local coder model through the primary router pipeline.
"""

import logging
from backend.router.coder_service import generate_code
from backend.coding_agent.patcher import apply_patch

logger = logging.getLogger("sovereign.coding_agent.repair_loop")


async def generate_patch(
    repo_path: str,
    task: str,
    file_path: str,
    context: str,
    error_log: str = "",
) -> str:
    """
    Generate a SEARCH/REPLACE patch for a file and apply it.

    Returns a success message or an error string.
    """
    prompt = f"""
You are a Software Engineering Repair Agent.
Task: {task}
File to modify: {file_path}

Current File Content:
```python
{context}
```
"""
    if error_log:
        prompt += f"\nTest Failure Log:\n```\n{error_log}\n```\nFix the bug causing this test failure."

    prompt += """
Generate a patch for this file.
Output exactly ONE patch block in this format (no markdown, no other text):
SEARCH:
<exact lines to replace>
REPLACE:
<new lines>
"""
    try:
        gen = await generate_code(prompt)
    except Exception as e:
        return f"Error: Code generation failed: {e}"

    raw = gen.code

    if "SEARCH:" not in raw or "REPLACE:" not in raw:
        # Try to salvage: if the model returned the entire new file, create from scratch
        logger.warning("Patch response missing SEARCH/REPLACE markers, attempting raw apply")
        return f"Error: Could not parse SEARCH/REPLACE block from model output."

    try:
        search_part = raw.split("SEARCH:")[1].split("REPLACE:")[0].strip()
        replace_part = raw.split("REPLACE:")[1].strip()

        # Remove markdown ticks if present
        for fence in ("```python", "```"):
            if search_part.startswith(fence):
                search_part = search_part[len(fence):].strip()
            if replace_part.startswith(fence):
                replace_part = replace_part[len(fence):].strip()

        if search_part.endswith("```"):
            search_part = search_part[:-3].strip()
        if replace_part.endswith("```"):
            replace_part = replace_part[:-3].strip()

        return apply_patch(repo_path, file_path, search_part, replace_part)
    except Exception as e:
        return f"Error parsing patch: {e}"
