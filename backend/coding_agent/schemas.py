from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class TaskPlan(BaseModel):
    steps: List[str] = Field(description="Step-by-step plan to implement the feature")
    affected_files: List[str] = Field(description="Files that will likely be modified")

class PatchRequest(BaseModel):
    file_path: str = Field(description="Path to the file to modify")
    search_text: str = Field(description="Exact text block to replace")
    replace_text: str = Field(description="New text block")

class TestResult(BaseModel):
    success: bool
    output: str
    error: Optional[str] = None
