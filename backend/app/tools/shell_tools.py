import ctypes
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from app.core.exceptions import ToolError
from app.tools.base import BaseTool

_DEFAULT_TIMEOUT_SECONDS = 10
_MAX_OUTPUT_CHARS = 12000
_DANGEROUS_EXECUTABLES = {
    "rm",
    "rmdir",
    "del",
    "erase",
    "format",
    "shutdown",
    "reboot",
    "mkfs",
    "diskpart",
    "reg",
    "takeown",
    "icacls",
}
_DANGEROUS_TOKENS = {
    "rm",
    "rm.exe",
    "rmdir",
    "del",
    "erase",
    "format",
    "shutdown",
    "reboot",
    "mkfs",
    "diskpart",
}
_SHELL_CONTROL_TOKENS = {"|", "||", "&", "&&", ";", "<", ">", ">>", "2>", "`"}


class RunCommandArgs(BaseModel):
    command: str = Field(min_length=1, max_length=500)
    cwd: str
    project_path: str | None = None
    timeout_seconds: int = Field(default=_DEFAULT_TIMEOUT_SECONDS, ge=1, le=30)


class RunCommandTool(BaseTool):
    name = "run_command"
    description = "Run a restricted read-only development command inside a project directory with timeout and captured output."
    args_schema = RunCommandArgs

    def run(self, **kwargs: Any) -> dict[str, Any]:
        args = self.validate_args(kwargs)
        assert isinstance(args, RunCommandArgs)

        cwd = self._resolve_cwd(args.cwd, args.project_path)
        tokens = self._parse_command(args.command)
        self._validate_safe_command(tokens, args.command)

        try:
            # shell=False is the main safety boundary here: operators such as
            # pipes, redirects, and command chaining are never interpreted by a
            # shell. The command must be a single executable plus plain args.
            completed = subprocess.run(
                tokens,
                cwd=str(cwd),
                text=True,
                capture_output=True,
                timeout=args.timeout_seconds,
                check=False,
            )
        except FileNotFoundError as exc:
            raise ToolError(f"Command executable not found: {tokens[0]}") from exc
        except subprocess.TimeoutExpired as exc:
            return {
                "command": args.command,
                "cwd": str(cwd),
                "timed_out": True,
                "timeout_seconds": args.timeout_seconds,
                "exit_code": None,
                "stdout": self._truncate(exc.stdout or ""),
                "stderr": self._truncate(exc.stderr or f"Command timed out after {args.timeout_seconds} seconds"),
            }

        return {
            "command": args.command,
            "cwd": str(cwd),
            "timed_out": False,
            "timeout_seconds": args.timeout_seconds,
            "exit_code": completed.returncode,
            "stdout": self._truncate(completed.stdout),
            "stderr": self._truncate(completed.stderr),
        }

    def _resolve_cwd(self, cwd: str, project_path: str | None) -> Path:
        cwd_path = Path(cwd).expanduser().resolve()
        if not cwd_path.exists():
            raise ToolError(f"Working directory does not exist: {cwd_path}")
        if not cwd_path.is_dir():
            raise ToolError(f"Working directory is not a directory: {cwd_path}")

        if project_path is None:
            return cwd_path

        project_root = Path(project_path).expanduser().resolve()
        if not project_root.exists() or not project_root.is_dir():
            raise ToolError(f"Project path is not a directory: {project_root}")

        # All command execution must remain inside the declared project root.
        # This prevents an Agent from using an innocent-looking cwd argument to
        # inspect or mutate files elsewhere on the developer machine.
        try:
            cwd_path.relative_to(project_root)
        except ValueError as exc:
            raise ToolError("Working directory is outside the allowed project root") from exc
        return cwd_path

    def _parse_command(self, command: str) -> list[str]:
        cleaned = command.strip()
        if not cleaned:
            raise ToolError("Command cannot be empty")
        if sys.platform == "win32":
            return self._parse_windows_command(cleaned)
        return self._parse_posix_command(cleaned)

    def _parse_posix_command(self, command: str) -> list[str]:
        try:
            return shlex.split(command, posix=True)
        except ValueError as exc:
            raise ToolError(f"Failed to parse command: {exc}") from exc

    def _parse_windows_command(self, command: str) -> list[str]:
        # Windows command-line quoting differs from POSIX shells. Calling the
        # native parser preserves paths such as `D:\Python\python.exe` while
        # still stripping quotes around arguments like `-c "print(1)"`.
        argc = ctypes.c_int()
        shell32 = ctypes.windll.shell32
        kernel32 = ctypes.windll.kernel32
        shell32.CommandLineToArgvW.argtypes = [ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_int)]
        shell32.CommandLineToArgvW.restype = ctypes.POINTER(ctypes.c_wchar_p)
        kernel32.LocalFree.argtypes = [ctypes.c_void_p]
        kernel32.LocalFree.restype = ctypes.c_void_p
        argv = shell32.CommandLineToArgvW(command, ctypes.byref(argc))
        if not argv:
            raise ToolError("Failed to parse command")
        try:
            return [argv[index] for index in range(argc.value)]
        finally:
            kernel32.LocalFree(argv)

    def _validate_safe_command(self, tokens: list[str], raw_command: str) -> None:
        if not tokens:
            raise ToolError("Command cannot be empty")
        if "\n" in raw_command or "$(" in raw_command:
            raise ToolError("Shell control operators, pipes, redirects, and command substitution are not allowed")
        if any(token in _SHELL_CONTROL_TOKENS for token in tokens):
            raise ToolError("Shell control operators, pipes, redirects, and command substitution are not allowed")

        executable = Path(tokens[0]).name.lower()
        normalized_tokens = {Path(token).name.lower() for token in tokens}
        if executable in _DANGEROUS_EXECUTABLES or normalized_tokens & _DANGEROUS_TOKENS:
            raise ToolError(f"Dangerous command is not allowed: {tokens[0]}")

        lowered = raw_command.lower()
        if "curl" in lowered and "| sh" in lowered:
            raise ToolError("Piping curl output to a shell is not allowed")
        if "invoke-webrequest" in lowered and ("iex" in lowered or "invoke-expression" in lowered):
            raise ToolError("Downloading and executing scripts is not allowed")

    def _truncate(self, value: str | bytes | None) -> str:
        if value is None:
            return ""
        text = value.decode(errors="replace") if isinstance(value, bytes) else value
        if len(text) <= _MAX_OUTPUT_CHARS:
            return text
        return text[:_MAX_OUTPUT_CHARS] + "...[truncated]"
