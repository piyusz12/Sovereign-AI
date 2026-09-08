import json
import re
from backend.router.coder_service import generate_code
from backend.coding_agent.schemas import TaskPlan
from pydantic import ValidationError


def _extract_json(text: str) -> str:
    """Extract the first JSON object from a model response."""
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE)
    if fenced:
        return fenced.group(1)
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("model response did not contain a JSON object")
    return text[start:end + 1]

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
        data = json.loads(_extract_json(gen.code))
        plan = TaskPlan(**data)
        if not plan.steps or not plan.affected_files:
            raise ValueError("plan must contain steps and affected_files")
        return plan
    except (json.JSONDecodeError, ValidationError, ValueError) as exc:
        raise RuntimeError(f"Coding model returned an unusable plan: {exc}") from exc
