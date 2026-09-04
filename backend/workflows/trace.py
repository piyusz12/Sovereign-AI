"""
Sovereign AI Workbench — Workflow Tracing

Provides data structures to record and report the step-by-step
execution of flagship workflows for UI presentation and auditing.
"""

from pydantic import BaseModel, Field
from typing import Any, List, Optional
from datetime import datetime

class WorkflowStep(BaseModel):
    step_number: int
    name: str
    status: str = Field(description="success, error, or pending")
    details: Optional[str] = None
    duration_ms: float = 0.0

class WorkflowTrace(BaseModel):
    workflow_id: str
    name: str
    status: str = "running"
    start_time: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    end_time: Optional[str] = None
    steps: List[WorkflowStep] = Field(default_factory=list)
    deliverables: List[str] = Field(default_factory=list)
    error: Optional[str] = None

    def add_step(self, name: str, status: str = "success", details: str = None, duration_ms: float = 0.0):
        step_num = len(self.steps) + 1
        self.steps.append(
            WorkflowStep(
                step_number=step_num,
                name=name,
                status=status,
                details=details,
                duration_ms=duration_ms
            )
        )

    def complete(self, status: str = "success", error: str = None):
        self.status = status
        self.error = error
        self.end_time = datetime.utcnow().isoformat()
