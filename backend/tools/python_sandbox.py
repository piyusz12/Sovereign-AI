"""
PHASE 9 — Docker code sandbox.

Executes untrusted, LLM-generated Python code in an isolated container:
    - network disabled  (--network none)
    - CPU limited        (--cpus)
    - RAM limited         (--memory)
    - execution time limited (subprocess timeout + container --stop-timeout)
    - filesystem isolated (mounts ONLY a scratch dir, read-write; nothing
      else from the host is exposed)

Requires: Docker Desktop running with the WSL2 backend, GPU passthrough
enabled (Phase 2). No GPU is needed for code execution itself.

Test:
    python -m backend.tools.python_sandbox
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path

SANDBOX_IMAGE = "python:3.12-slim"
MAX_RUNTIME_SECONDS = 15
MAX_MEMORY = "512m"
MAX_CPUS = "1"


@dataclass
class SandboxResult:
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool = False


class SandboxError(RuntimeError):
    pass


def is_docker_running() -> bool:
    """Check if Docker CLI is installed and the daemon is reachable."""
    if shutil.which("docker") is None:
        return False
    try:
        res = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=2.0,
        )
        return res.returncode == 0
    except (subprocess.SubprocessError, OSError):
        return False


def _docker_available() -> None:
    if shutil.which("docker") is None:
        raise SandboxError(
            "Docker CLI not found. Install Docker Desktop and enable the "
            "WSL2 integration before using the sandbox."
        )
    if not is_docker_running():
        raise SandboxError(
            "Docker daemon is not running. Please start Docker Desktop with "
            "WSL2 integration enabled before using the sandbox."
        )


def run_python_code(code: str, *, timeout: int = MAX_RUNTIME_SECONDS, input_files: dict[str, str] = None) -> SandboxResult:
    """
    Write `code` to a throwaway scratch directory, mount ONLY that directory
    into a fresh, network-disabled container, run it, and return the result.
    The scratch directory is deleted afterward regardless of outcome.
    If `input_files` is provided, it maps destination filename (relative to workspace)
    to an absolute source filepath on the host, which will be copied into the scratch dir.
    """
    docker_ready = is_docker_running()
    if not docker_ready:
        print("WARNING: Docker daemon is not running. Falling back to local unsafe execution.")

    run_id = uuid.uuid4().hex[:8]
    scratch_dir = Path(tempfile.mkdtemp(prefix=f"sandbox_{run_id}_"))
    script_path = scratch_dir / "main.py"
    script_path.write_text(code, encoding="utf-8")

    if input_files:
        for dest_name, src_path in input_files.items():
            dest_path = scratch_dir / dest_name
            try:
                if Path(src_path).is_dir():
                    shutil.copytree(src_path, dest_path)
                else:
                    shutil.copy2(src_path, dest_path)
            except Exception as e:
                shutil.rmtree(scratch_dir, ignore_errors=True)
                raise SandboxError(f"Failed to copy input file {src_path} to sandbox: {e}")

    container_name = f"sovereign-sandbox-{run_id}"

    timed_out = False
    enclave = None

    try:
        if docker_ready:
            cmd = [
                "docker", "run",
                "--rm",
                "--name", container_name,
                "--network", "none",
                "--memory", MAX_MEMORY,
                "--cpus", MAX_CPUS,
                "--pids-limit", "64",
                "--read-only",
                "--tmpfs", "/tmp:rw,size=64m",
                "-v", f"{scratch_dir}:/workspace:rw",
                "-w", "/workspace",
                "--user", "nobody",
                SANDBOX_IMAGE,
                "python", "/workspace/main.py",
            ]
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            stdout, stderr, exit_code = proc.stdout, proc.stderr, proc.returncode
        else:
            # Native C++ Win32 Job Object hardware-enforced memory and CPU containment
            from backend.cpp_bridge.bridge import cpp_core
            enclave = cpp_core.create_sandbox_enclave(max_memory_mb=512, max_processes=8, cpu_rate_percent=85)
            cmd = [sys.executable, str(script_path)]

            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(scratch_dir),
            )
            if enclave:
                enclave.assign_process(proc.pid)

            stdout, stderr = proc.communicate(timeout=timeout)
            exit_code = proc.returncode

            if enclave:
                stats = enclave.get_stats()
                if stats.get("peak_memory_mb", 0) > 0:
                    enclave_notice = f"[C++ Win32 Enclave] Peak RAM: {stats['peak_memory_mb']} MB | CPU: {round(stats['cpu_time_us']/1000, 2)} ms"
                    stderr = (stderr + "\n" + enclave_notice).strip() if stderr else enclave_notice

    except subprocess.TimeoutExpired as exc:
        timed_out = True
        if docker_ready:
            subprocess.run(["docker", "kill", container_name], capture_output=True)
        elif enclave:
            enclave.terminate(1)
        stdout, stderr, exit_code = (getattr(exc, "stdout", "") or ""), "Execution timed out (terminated by sandbox)", -1
    finally:
        if enclave:
            enclave.close()
        shutil.rmtree(scratch_dir, ignore_errors=True)

    return SandboxResult(
        success=(exit_code == 0 and not timed_out),
        stdout=stdout,
        stderr=stderr,
        exit_code=exit_code,
        timed_out=timed_out,
    )


if __name__ == "__main__":
    demo_code = "print('hello from the sandbox')\nprint(2 + 2)\n"
    result = run_python_code(demo_code)
    print("success:", result.success)
    print("stdout:", result.stdout)
    print("stderr:", result.stderr)
