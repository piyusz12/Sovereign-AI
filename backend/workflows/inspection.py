"""
Sovereign AI Workbench — Flagship Inspection Workflow

Orchestrates: Vision -> RAG -> Reasoning -> Sandbox -> Deliverable Generation
"""

import logging
import json
from pathlib import Path
from backend.workflows.trace import WorkflowTrace

from backend.agent.tools_registry import _execute_vision_async
from backend.rag.adaptive import adaptive_rag

from backend.agent.code_repair_loop import generate_and_verify
from backend.generators.service import deliverable_service
from backend.router.ollama_client import ollama_client
from backend.settings import settings

logger = logging.getLogger("sovereign.workflows.inspection")

async def run_inspection_workflow(trace: WorkflowTrace, user_role: str, inputs: dict):
    file_path = inputs.get("file_path")
    query = inputs.get("query", "Analyze this inspection report.")
    
    if not file_path:
        raise ValueError("No file_path provided for inspection workflow.")
        
    trace.add_step("Document Ingestion", status="success", details=f"Received: {Path(file_path).name}")
    
    # 1. Vision / OCR
    vision_start = trace.steps[-1].duration_ms
    vision_res = await _execute_vision_async(f"{query} Extract key findings, measurements, and equipment tags as structured JSON.", str(file_path))
    if not vision_res.success:
        raise Exception(f"Vision analysis failed: {vision_res.error}")
    
    trace.add_step("Vision Extraction", status="success", details="Extracted findings via Qwen3-VL-8B")
    extracted_text = vision_res.output
    
    # 2. RAG Search
    rag_res = await adaptive_rag.query(extracted_text, user_role=user_role, top_k=3)
    snippets = [r.get("text", "") for r in rag_res.sources]
    trace.add_step("Internal Knowledge Retrieval", status="success", details=f"Retrieved {len(snippets)} relevant SOP sections")
    
    # 3. Agent Reasoning (Determining calculation)
    reasoning_prompt = f"""
    Based on the inspection findings and the internal SOP, do we need to calculate anything (like wear, percentage loss)?
    Inspection: {extracted_text}
    SOP: {' | '.join(snippets)}
    
    If calculation is needed, output Python code to perform it and print a JSON dictionary of the results. 
    If no calculation is needed, output Python code that just prints {{"status": "ok"}}.
    """
    
    # 4. Sandbox Execution
    repair_res = await generate_and_verify(reasoning_prompt)
    if not repair_res.success:
        raise Exception(f"Sandbox calculation failed after {repair_res.attempts} attempts: {repair_res.stderr}")
        
    trace.add_step("Sandbox Execution", status="success", details=f"Executed calculations in {repair_res.attempts} attempt(s)")
    
    # 5. Deliverable Generation
    # Parse calculation output
    calc_output = {}
    try:
        # attempt to parse the printed stdout from the sandbox
        for line in repair_res.stdout.split('\n'):
            if line.strip().startswith('{'):
                calc_output = json.loads(line.strip())
                break
    except:
        pass
        
    doc_payload = {
        "inspection_data": {"Raw Findings": extracted_text, "Calculations": str(calc_output)},
        "analysis": "Based on the SOP, the findings have been processed.",
        "recommendation": "Review required.",
        "sources": [r.get("document_id", "unknown") for r in rag_res.sources]
    }
    
    docx_path, err = await deliverable_service.create_and_validate_docx(
        title="Inspection Approval Note", content=doc_payload, template="approval_note"
    )
    if err:
        raise Exception(f"Failed to generate DOCX: {err}")
    trace.deliverables.append(docx_path)
    trace.add_step("Approval Note Generated", status="success", details=Path(docx_path).name)
    
    xlsx_path, err = await deliverable_service.create_and_validate_xlsx(
        title="Inspection Analysis", data=[{"Finding": extracted_text, "Calc": str(calc_output)}]
    )
    if err:
        raise Exception(f"Failed to generate XLSX: {err}")
    trace.deliverables.append(xlsx_path)
    trace.add_step("Excel Analysis Generated", status="success", details=Path(xlsx_path).name)
