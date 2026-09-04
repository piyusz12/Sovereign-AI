import asyncio
import os
import shutil
from pathlib import Path
from backend.tools.python_sandbox import is_docker_running, SandboxError, SANDBOX_IMAGE, MAX_MEMORY, MAX_CPUS
import subprocess
import uuid

def run_tests_in_sandbox(repo_path: str, test_command: str = "python -m pytest") -> dict:
    """
    Copies the repo to a scratch directory and runs the test_command in the sandbox.
    """
    docker_ready = is_docker_running()
    
    run_id = uuid.uuid4().hex[:8]
    import tempfile
    scratch_dir = Path(tempfile.mkdtemp(prefix=f"sandbox_{run_id}_"))
    
    try:
        # Copy the entire repo into scratch space
        shutil.copytree(repo_path, scratch_dir, dirs_exist_ok=True)
    except Exception as e:
        shutil.rmtree(scratch_dir, ignore_errors=True)
        return {"success": False, "output": "", "error": f"Failed to mount repo: {e}"}

    container_name = f"sovereign-sandbox-{run_id}"

    if docker_ready:
        cmd = [
            "docker", "run", "--rm",
            "--name", container_name,
            "--network", "none",
            "--memory", MAX_MEMORY,
            "--cpus", MAX_CPUS,
            "-v", f"{scratch_dir}:/workspace:rw",
            "-w", "/workspace",
            SANDBOX_IMAGE,
            "bash", "-c", f"pip install -q pytest && {test_command}"
        ]
    else:
        # Fallback local
        cmd = ["bash", "-c", test_command] if os.name != 'nt' else ["cmd", "/c", test_command]

    timed_out = False
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(scratch_dir) if not docker_ready else None,
        )
        stdout, stderr, exit_code = proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        if docker_ready:
            subprocess.run(["docker", "kill", container_name], capture_output=True)
        stdout, stderr, exit_code = (exc.stdout or ""), (exc.stderr or "execution timed out"), -1
    finally:
        shutil.rmtree(scratch_dir, ignore_errors=True)

    return {
        "success": (exit_code == 0 and not timed_out),
        "output": stdout,
        "error": stderr
    }
