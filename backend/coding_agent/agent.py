import logging
from pathlib import Path
from backend.coding_agent.repository import list_files, read_file
from backend.coding_agent.planner import create_plan
from backend.coding_agent.repair_loop import generate_patch
from backend.coding_agent.executor import run_tests_in_sandbox

logger = logging.getLogger(__name__)

async def run_coding_agent(repo_path: str, task: str) -> dict:
    """
    Main orchestrator for the True Coding Agent.
    """
    repo = Path(repo_path).resolve()
    if not repo.is_dir():
        return {"status": "error", "trace": [], "output": "", "error": f"Repository not found: {repo_path}"}

    # 1. Repository Understanding
    logger.info("Listing repository files...")
    files = list_files(repo_path)
    
    # 2. Planning
    logger.info("Generating implementation plan...")
    try:
        plan = await create_plan(task, files)
    except Exception as exc:
        return {"status": "error", "trace": [], "output": "", "error": str(exc)}
    
    trace_events = []
    trace_events.append(f"Plan created: {plan.steps}")
    
    # 3. Patching and Execution Loop
    if not plan.affected_files:
        return {"status": "error", "trace": trace_events, "output": "", "error": "Plan contains no affected files"}

    affected_files = list(dict.fromkeys(plan.affected_files))
    for file_to_edit in affected_files:
        logger.info(f"Targeting file: {file_to_edit}")
        content = read_file(repo_path, file_to_edit)
        if content.startswith("Error: File "):
            content = ""
        
        # Initial code generation (Attempt 1)
        patch_result = await generate_patch(repo_path, task, file_to_edit, content)
        trace_events.append(f"Patch applied to {file_to_edit}: {patch_result}")
        if not patch_result.startswith("Successfully "):
            return {"status": "error", "trace": trace_events, "output": "", "error": patch_result}
        
    # 4. Sandbox Testing & Repair Loop
    logger.info("Running tests in sandbox...")
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        test_res = run_tests_in_sandbox(repo_path, "python -m pytest")
        
        if test_res["success"]:
            trace_events.append(f"Tests passed on attempt {attempt}")
            return {"status": "success", "trace": trace_events, "output": test_res["output"]}
            
        trace_events.append(f"Test failure on attempt {attempt}:\n{test_res['output']}\n{test_res['error']}")
        
        if attempt == max_retries:
            break
            
        # Repair (For simplicity in demo, we retry patching the first affected file)
        logger.info(f"Test failed. Initiating repair attempt {attempt}...")
        for file_to_edit in affected_files:
            content = read_file(repo_path, file_to_edit)
            if content.startswith("Error: File "):
                content = ""
            error_log = f"{test_res.get('output', '')}\n{test_res.get('error', '')}"[-12000:]
            patch_result = await generate_patch(repo_path, task, file_to_edit, content, error_log=error_log)
            trace_events.append(f"Repair patch applied to {file_to_edit}: {patch_result}")
            if not patch_result.startswith("Successfully "):
                return {"status": "error", "trace": trace_events, "output": test_res["output"], "error": patch_result}

    return {"status": "error", "trace": trace_events, "output": test_res["output"], "error": test_res.get("error", "Tests failed")}
