"""
Sovereign AI Workbench — Workflow Engine

Orchestrates the flagship workflows by accepting inputs, selecting
the appropriate workflow based on intent, and returning the structured trace.
"""

import logging
import uuid
from typing import Any

from backend.workflows.trace import WorkflowTrace

logger = logging.getLogger("sovereign.workflows.engine")

class WorkflowEngine:
    """Manages execution of flagship demo workflows."""
    
    def __init__(self):
        # We will import workflows dynamically or bind them in registry
        self._workflows = {}

    def register(self, name: str, handler):
        self._workflows[name] = handler

    async def execute(self, user_role: str, request_type: str, inputs: dict[str, Any]) -> WorkflowTrace:
        """Execute a named workflow and return its trace and deliverables."""
        trace = WorkflowTrace(workflow_id=str(uuid.uuid4()), name=request_type)
        
        if request_type not in self._workflows:
            trace.add_step("Workflow Routing", status="error", details=f"Unknown workflow: {request_type}")
            trace.complete(status="error", error=f"Workflow '{request_type}' not found.")
            return trace

        handler = self._workflows[request_type]
        logger.info(f"Executing workflow '{request_type}' for role '{user_role}'")
        
        try:
            # Each workflow handler is responsible for appending to the trace
            await handler(trace, user_role, inputs)
            trace.complete(status="success")
        except Exception as e:
            logger.error(f"Workflow '{request_type}' failed: {e}", exc_info=True)
            trace.add_step("Workflow Execution", status="error", details=str(e))
            trace.complete(status="error", error=str(e))
            
        return trace

workflow_engine = WorkflowEngine()
