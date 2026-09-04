"""
Run with: pytest tests/test_sandbox.py -v
Requires Docker to be running. Does NOT require Ollama/the coder model —
these tests only exercise Phase 9 (the sandbox) directly.
"""

import pytest

from backend.tools.python_sandbox import is_docker_running, run_python_code

pytestmark = pytest.mark.skipif(
    not is_docker_running(),
    reason="Docker daemon not running (requires Docker Desktop with WSL2 integration)",
)


def test_basic_execution_succeeds():
    result = run_python_code("print('ok')")
    assert result.success
    assert "ok" in result.stdout


def test_syntax_error_is_reported_not_crashed():
    result = run_python_code("def broken(:\n    pass")
    assert not result.success
    assert result.exit_code != 0
    assert result.stderr  # some error text came back


def test_network_is_disabled():
    code = (
        "import socket\n"
        "try:\n"
        "    socket.create_connection(('8.8.8.8', 53), timeout=3)\n"
        "    print('NETWORK_REACHABLE')\n"
        "except Exception as e:\n"
        "    print('NETWORK_BLOCKED:', e)\n"
    )
    result = run_python_code(code)
    assert "NETWORK_BLOCKED" in result.stdout
    assert "NETWORK_REACHABLE" not in result.stdout


def test_infinite_loop_times_out():
    result = run_python_code("while True:\n    pass", timeout=5)
    assert not result.success
    assert result.timed_out


def test_filesystem_outside_workspace_is_not_writable():
    code = (
        "try:\n"
        "    open('/etc/sandbox_test', 'w').write('x')\n"
        "    print('WRITE_SUCCEEDED')\n"
        "except Exception as e:\n"
        "    print('WRITE_BLOCKED:', e)\n"
    )
    result = run_python_code(code)
    assert "WRITE_BLOCKED" in result.stdout
