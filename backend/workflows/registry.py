"""
Sovereign AI Workbench — Workflow Registry

Registers all flagship workflows with the Workflow Engine.
"""

from backend.workflows.engine import workflow_engine

def init_workflows():
    """Register all available workflows."""
    
    # We delay imports to avoid circular dependencies
    from backend.workflows.inspection import run_inspection_workflow
    from backend.workflows.coding import run_coding_workflow
    
    workflow_engine.register("inspection", run_inspection_workflow)
    workflow_engine.register("coding", run_coding_workflow)
