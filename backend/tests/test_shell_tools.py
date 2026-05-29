import sys
from pathlib import Path

import pytest

from app.core.exceptions import ToolError
from app.tools.shell_tools import RunCommandTool


def test_run_command_executes_inside_project_and_captures_output(tmp_path: Path) -> None:
    result = RunCommandTool().run(
        command=f"{sys.executable} -c \"print('hello shell')\"",
        cwd=str(tmp_path),
        project_path=str(tmp_path),
    )

    assert result["exit_code"] == 0
    assert result["timed_out"] is False
    assert "hello shell" in result["stdout"]
    assert result["stderr"] == ""


def test_run_command_rejects_cwd_outside_project(tmp_path: Path) -> None:
    outside = tmp_path.parent

    with pytest.raises(ToolError, match="outside"):
        RunCommandTool().run(command=f"{sys.executable} --version", cwd=str(outside), project_path=str(tmp_path))


def test_run_command_rejects_dangerous_commands(tmp_path: Path) -> None:
    with pytest.raises(ToolError, match="Dangerous command"):
        RunCommandTool().run(command="rm -rf .", cwd=str(tmp_path), project_path=str(tmp_path))


def test_run_command_rejects_shell_control_operators(tmp_path: Path) -> None:
    with pytest.raises(ToolError, match="Shell control"):
        RunCommandTool().run(command=f"{sys.executable} --version && {sys.executable} --version", cwd=str(tmp_path))


def test_run_command_returns_timeout_result(tmp_path: Path) -> None:
    result = RunCommandTool().run(
        command=f"{sys.executable} -c \"import time; time.sleep(2)\"",
        cwd=str(tmp_path),
        project_path=str(tmp_path),
        timeout_seconds=1,
    )

    assert result["timed_out"] is True
    assert result["exit_code"] is None
    assert "timed out" in result["stderr"].lower()


def test_run_command_captures_nonzero_exit_code(tmp_path: Path) -> None:
    result = RunCommandTool().run(
        command=f"{sys.executable} -c \"import sys; sys.stderr.write('bad'); sys.exit(7)\"",
        cwd=str(tmp_path),
        project_path=str(tmp_path),
    )

    assert result["exit_code"] == 7
    assert result["stderr"] == "bad"
