from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from app.core.exceptions import ToolError
from app.tools.base import BaseTool

DEFAULT_MAX_FILE_BYTES = 1_000_000
IGNORED_DIRS = {".git", "node_modules", ".venv", "venv", "dist", "build", "__pycache__", ".next"}


class ListFilesArgs(BaseModel):
    project_path: str
    max_files: int = Field(default=500, ge=1, le=5000)


class ReadFileArgs(BaseModel):
    file_path: str
    project_path: str | None = None
    max_bytes: int = Field(default=DEFAULT_MAX_FILE_BYTES, ge=1, le=5_000_000)


def _resolve_existing_dir(path: str) -> Path:
    root = Path(path).expanduser().resolve()
    if not root.exists():
        raise ToolError(f"Project path does not exist: {path}")
    if not root.is_dir():
        raise ToolError(f"Project path is not a directory: {path}")
    return root


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _resolve_file(file_path: str, project_path: str | None) -> tuple[Path, Path]:
    if project_path:
        root = _resolve_existing_dir(project_path)
        candidate = Path(file_path).expanduser()
        resolved = (root / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()
    else:
        resolved = Path(file_path).expanduser().resolve()
        root = resolved.parent

    if not resolved.exists():
        raise ToolError(f"File does not exist: {file_path}")
    if not resolved.is_file():
        raise ToolError(f"Path is not a file: {file_path}")
    if not _is_relative_to(resolved, root):
        raise ToolError("File path is outside the allowed project root")
    return root, resolved


def _looks_binary(path: Path) -> bool:
    sample = path.read_bytes()[:4096]
    if b"\x00" in sample:
        return True
    try:
        sample.decode("utf-8")
    except UnicodeDecodeError:
        return True
    return False


class ListFilesTool(BaseTool):
    name = "list_files"
    description = "List text/code files under a project path, ignoring common dependency and build directories."
    args_schema = ListFilesArgs

    def run(self, **kwargs: Any) -> dict[str, Any]:
        args = self.validate_args(kwargs)
        assert isinstance(args, ListFilesArgs)
        root = _resolve_existing_dir(args.project_path)
        files: list[str] = []

        for path in root.rglob("*"):
            if any(part in IGNORED_DIRS for part in path.relative_to(root).parts):
                continue
            if path.is_file():
                files.append(path.relative_to(root).as_posix())
            if len(files) >= args.max_files:
                break

        return {"project_path": str(root), "count": len(files), "files": files}


class ReadFileTool(BaseTool):
    name = "read_file"
    description = "Read a UTF-8 text file inside the project root with size and binary-file safeguards."
    args_schema = ReadFileArgs

    def run(self, **kwargs: Any) -> dict[str, Any]:
        args = self.validate_args(kwargs)
        assert isinstance(args, ReadFileArgs)
        root, file_path = _resolve_file(args.file_path, args.project_path)
        size = file_path.stat().st_size

        if size > args.max_bytes:
            raise ToolError(f"File is too large to read: {size} bytes, limit is {args.max_bytes} bytes")
        if _looks_binary(file_path):
            raise ToolError(f"Refusing to read binary file: {file_path}")

        content = file_path.read_text(encoding="utf-8")
        return {
            "project_path": str(root),
            "file_path": str(file_path),
            "relative_path": file_path.relative_to(root).as_posix(),
            "size": size,
            "content": content,
        }
