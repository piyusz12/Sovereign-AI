"""
Connects PHASE 8 (coder_service) and PHASE 9 (python_sandbox) into the
self-correction loop described in the architecture:

    Generate -> Execute -> Observe -> error? -> Fix -> Execute again
                                     -> ok?    -> Verify

This is what a LangGraph node will call in Phase 11. Kept standalone here
so Phase 8/9 can be demoed and tested before the agent graph exists.

Test:
    python -m backend.agent.code_repair_loop "read a CSV called data.csv \\
        and print the average of the 'temperature' column, handling the \\
        file not existing"
"""

from __future__ import annotations

import asyncio
import sys
from dataclasses import dataclass, field

from backend.router.coder_service import CoderServiceError, generate_code
from backend.tools.python_sandbox import SandboxError, run_python_code

MAX_ATTEMPTS = 3


@dataclass
class RepairLoopResult:
    success: bool
    final_code: str
    stdout: str
    stderr: str
    attempts: int
    history: list = field(default_factory=list)  # list of dicts per attempt


async def generate_and_verify(task_description: str, context: str = "", *, max_attempts: int = MAX_ATTEMPTS, input_files: dict[str, str] = None) -> RepairLoopResult:
    if context:
        task_description += f"\n\nHigh-level verification failures from previous attempts:\n{context}"

    history = []
    code = ""
    stdout = ""
    stderr = ""

    import time
    for attempt in range(1, max_attempts + 1):
        gen_start = time.time()
        try:
            if attempt == 1:
                gen = await generate_code(task_description)
            else:
                gen = await generate_code(
                    task_description,
                    prior_code=code,
                    error_output=stderr,
                )
        except CoderServiceError as exc:
            history.append({"attempt": attempt, "stage": "generate", "error": str(exc), "generate_ms": (time.time() - gen_start) * 1000})
            break

        gen_ms = (time.time() - gen_start) * 1000
        code = gen.code

        exec_start = time.time()
        try:
            # Using asyncio.to_thread because run_python_code uses blocking subprocess.run
            result = await asyncio.to_thread(run_python_code, code, input_files=input_files)
        except SandboxError as exc:
            history.append({"attempt": attempt, "stage": "sandbox", "error": str(exc), "generate_ms": gen_ms, "sandbox_ms": (time.time() - exec_start) * 1000})
            break

        exec_ms = (time.time() - exec_start) * 1000
        stdout, stderr = result.stdout, result.stderr
        history.append(
            {
                "attempt": attempt,
                "stage": "execute",
                "success": result.success,
                "stdout": stdout,
                "stderr": stderr,
                "timed_out": result.timed_out,
                "generate_ms": gen_ms,
                "sandbox_ms": exec_ms,
            }
        )

        if result.success:
            return RepairLoopResult(
                success=True,
                final_code=code,
                stdout=stdout,
                stderr=stderr,
                attempts=attempt,
                history=history,
            )

    return RepairLoopResult(
        success=False,
        final_code=code,
        stdout=stdout,
        stderr=stderr,
        attempts=len(history),
        history=history,
    )


if __name__ == "__main__":
    task = " ".join(sys.argv[1:]) or "print the first 10 fibonacci numbers"
    
    # Run the async loop
    outcome = asyncio.run(generate_and_verify(task))
    
    print(f"success: {outcome.success} (attempts: {outcome.attempts})")
    print("--- final code ---")
    print(outcome.final_code)
    print("--- stdout ---")
    print(outcome.stdout)
    if not outcome.success:
        print("--- stderr ---")
        print(outcome.stderr)
