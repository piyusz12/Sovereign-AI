import asyncio
from backend.router.coder_service import generate_code
from backend.coding_agent.patcher import apply_patch
from backend.coding_agent.executor import run_tests_in_sandbox

async def generate_patch(repo_path: str, task: str, file_path: str, context: str, error_log: str = "") -> str:
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
Output exactly ONE patch block in this format:
SEARCH:
<exact lines to replace>
REPLACE:
<new lines>
"""
    gen = await generate_code(prompt)
    raw = gen.code
    
    if "SEARCH:" not in raw or "REPLACE:" not in raw:
        return "Error: Could not parse SEARCH/REPLACE block."
        
    try:
        search_part = raw.split("SEARCH:")[1].split("REPLACE:")[0].strip()
        replace_part = raw.split("REPLACE:")[1].strip()
        # Remove markdown ticks if present
        if search_part.startswith("```python"): search_part = search_part[9:].strip()
        if search_part.startswith("```"): search_part = search_part[3:].strip()
        if search_part.endswith("```"): search_part = search_part[:-3].strip()
        
        if replace_part.startswith("```python"): replace_part = replace_part[9:].strip()
        if replace_part.startswith("```"): replace_part = replace_part[3:].strip()
        if replace_part.endswith("```"): replace_part = replace_part[:-3].strip()
        
        return apply_patch(repo_path, file_path, search_part, replace_part)
    except Exception as e:
        return f"Error parsing patch: {str(e)}"
