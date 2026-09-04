import json
from backend.router.coder_service import generate_code
from backend.coding_agent.schemas import TaskPlan
from pydantic import ValidationError

async def create_plan(request: str, repo_files: list[str]) -> TaskPlan:
    """
    Given a user request and a list of repository files, generates a plan.
    """
    prompt = f"""
You are a Software Engineering Planning Agent.
The user wants to implement the following request: "{request}"

The repository contains the following files:
{json.dumps(repo_files, indent=2)}

Create a step-by-step implementation plan. 
Output ONLY valid JSON matching this schema:
{{
    "steps": ["step 1", "step 2", ...],
    "affected_files": ["app/api.py", ...]
}}
"""
    # Ask the local coding model to generate the JSON plan
    gen = await generate_code(prompt)
    try:
        # Strip potential markdown blocks
        raw_json = gen.code
        if "```json" in raw_json:
            raw_json = raw_json.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_json:
            raw_json = raw_json.split("```")[1].split("```")[0].strip()
            
        data = json.loads(raw_json)
        return TaskPlan(**data)
    except (json.JSONDecodeError, ValidationError) as e:
        # Fallback if model fails to format
        return TaskPlan(
            steps=[f"Failed to parse plan: {e}", "Proceed manually"],
            affected_files=[]
        )
