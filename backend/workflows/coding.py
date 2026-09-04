"""
Sovereign AI Workbench — Flagship Coding Workflow

Orchestrates: Code Gen -> Sandbox Exec -> Repair Loop -> Deliverables
"""

import logging
from pathlib import Path
from backend.workflows.trace import WorkflowTrace

from backend.agent.code_repair_loop import generate_and_verify
from backend.generators.service import deliverable_service

logger = logging.getLogger("sovereign.workflows.coding")

async def run_coding_workflow(trace: WorkflowTrace, user_role: str, inputs: dict):
    query = inputs.get("query", "Analyze the data and create a script.")
    file_path = inputs.get("file_path", "")
    
    trace.add_step("Workflow Initiated", status="success", details="Coding & Data Analysis Workflow")
    
    prompt = query
    if file_path:
        prompt += f"\n\nAssume the data file is located at '{file_path}'. Write python code to analyze it, detect anomalies, and print the results as JSON."
    
    # 1. Code Generation & Sandbox Repair Loop
    trace.add_step("Code Generation & Sandbox Execution", status="pending")
    repair_res = await generate_and_verify(prompt, max_attempts=3)
    
    if not repair_res.success:
        trace.steps[-1].status = "error"
        trace.steps[-1].details = f"Failed after {repair_res.attempts} attempts"
        raise Exception(f"Code execution failed: {repair_res.stderr}")
        
    trace.steps[-1].status = "success"
    trace.steps[-1].details = f"Code succeeded after {repair_res.attempts} attempt(s)"
    
    # 2. Package Code Deliverable
    zip_path, err = await deliverable_service.create_and_validate_code_package(
        title="Analysis Script", 
        files={"main.py": repair_res.final_code, "requirements.txt": "pandas\nnumpy\n"}
    )
    if err:
        raise Exception(f"Failed to generate code package: {err}")
        
    trace.deliverables.append(zip_path)
    trace.add_step("Code Package Generated", status="success", details=Path(zip_path).name)
    
    # 3. Package Excel Deliverable
    xlsx_path, err = await deliverable_service.create_and_validate_xlsx(
        title="Anomaly Detection Results", 
        data=[{"Output": repair_res.stdout}]
    )
    if err:
        raise Exception(f"Failed to generate XLSX: {err}")
        
    trace.deliverables.append(xlsx_path)
    trace.add_step("Excel Report Generated", status="success", details=Path(xlsx_path).name)
