"""
Sovereign AI Workbench — Flagship Coding Workflow

Orchestrates: Code Gen -> Sandbox Exec -> Repair Loop -> Deliverables
"""

import logging
import shutil
import zipfile
from pathlib import Path
from backend.workflows.trace import WorkflowTrace
from backend.coding_agent.agent import run_coding_agent
from backend.generators.service import deliverable_service

logger = logging.getLogger("sovereign.workflows.coding")

async def run_coding_workflow(trace: WorkflowTrace, user_role: str, inputs: dict):
    query = inputs.get("query", "Analyze the data and create a script.")
    file_path = inputs.get("file_path", "")
    
    # Check if the user is pointing to a directory (the new Phase 22 feature)
    if file_path and Path(file_path).is_dir():
        trace.add_step("Repository Agent Initiated", status="success", details="Running True Coding Agent on " + file_path)
        
        result = await run_coding_agent(file_path, query)
        
        if result["status"] == "success":
            trace.add_step("Agent Success", status="success", details="Tests passed and code repaired.")
            # Package the modified repo
            output_dir = Path("data/output")
            output_dir.mkdir(parents=True, exist_ok=True)
            zip_path = output_dir / "modified_project.zip"
            shutil.make_archive(str(zip_path.with_suffix("")), 'zip', file_path)
            trace.deliverables.append(str(zip_path))
            return
        else:
            raise Exception(f"Coding Agent failed: {result['error']}\n{result['output']}")

    # Fallback to older logic for single files (Phase 21 data analysis)
    from backend.agent.code_repair_loop import generate_and_verify
    
    trace.add_step("Workflow Initiated", status="success", details="Coding & Data Analysis Workflow")
    
    prompt = query
    input_files = None
    if file_path:
        # Pass the file to the sandbox mapped to its basename
        file_name = Path(file_path).name
        input_files = {file_name: file_path}
        prompt += f"\n\nThe data file '{file_name}' is available in your current directory. Write a complete Python script to read it, analyze the data (calculating anomalies if asked), and print the final results as JSON to stdout. Ensure you handle potential KeyError or missing columns, or let the error surface so you can fix it in the next attempt."
    
    # 1. Code Generation & Sandbox Repair Loop
    trace.add_step("Code Generation & Sandbox Execution", status="pending")
    repair_res = await generate_and_verify(prompt, max_attempts=3, input_files=input_files)
    
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
