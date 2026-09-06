"""
Sovereign AI Workbench — Coder Service Bridge
"""
from typing import Optional
from dataclasses import dataclass

from backend.models import route_task, RoutingRequest, TaskType
from backend.model_gateway import model_gateway, GatewayInferenceRequest, ChatMessage

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
    Generate or repair Python code using the new Phase 27 Model Router.
    """
    context = ""
    if prior_code or error_output:
        context = "You are repairing broken code.\n"
        if prior_code:
            context += f"Prior Code:\n```python\n{prior_code}\n```\n"
        if error_output:
            context += f"Error Output:\n```text\n{error_output}\n```\n"

    try:
        # Phase 27: Ask the Model Router for a CODING model
        route = route_task(RoutingRequest(task_type=TaskType.CODING))
        
        request = GatewayInferenceRequest(
            model=route.selected_model,
            messages=[
                ChatMessage(role="system", content="You are a coding agent. Always return output enclosed in ```python code blocks."),
                ChatMessage(role="user", content=f"{context}\n\nTask: {task_description}")
            ],
            temperature=0.3
        )
        
        # We generate the text using the selected model
        response = await model_gateway.generate(request)
        response_text = response.content
        
        # Simple extraction of the code block
        if "```python" in response_text:
            code = response_text.split("```python")[1].split("```")[0].strip()
        elif "```" in response_text:
            code = response_text.split("```")[1].split("```")[0].strip()
        else:
            code = response_text.strip()
            
        if not code:
            raise CoderServiceError("Failed to extract code blocks from output.")
            
        return CodeGenerationResult(code=code)

    except Exception as e:
        if isinstance(e, CoderServiceError):
            raise
        raise CoderServiceError(f"Model generation failed: {e}")
