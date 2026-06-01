from collections.abc import Iterator
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from app.core.exceptions import ToolError
from app.core.project_paths import normalize_project_path
from app.tools.base import BaseTool

DEFAULT_MAX_FILE_BYTES = 1_000_000
IGNORED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    ".venv",
    "venv",
    "dist",
    "build",
    "__pycache__",
    ".next",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    "coverage",
    "htmlcov",
}


class ListFilesArgs(BaseModel):
    project_path: str
    max_files: int = Field(default=500, ge=1, le=5000)


class ReadFileArgs(BaseModel):
    file_path: str
    project_path: str | None = None
    max_bytes: int = Field(default=DEFAULT_MAX_FILE_BYTES, ge=1, le=5_000_000)


class ProjectTreeArgs(BaseModel):
    project_path: str
    max_depth: int = Field(default=3, ge=1, le=8)
    max_entries: int = Field(default=200, ge=1, le=1000)


class FindFilesArgs(BaseModel):
    project_path: str
    pattern: str = Field(min_length=1)
    max_results: int = Field(default=100, ge=1, le=1000)


def _resolve_existing_dir(path: str) -> Path:
    root = Path(normalize_project_path(path)).expanduser().resolve()
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
    try:
        sample = path.read_bytes()[:4096]
    except OSError:
        return True
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

        for path in iter_project_paths(root):
            if path.is_file():
                files.append(path.relative_to(root).as_posix())
                if len(files) >= args.max_files:
                    break

        return {"project_path": str(root), "count": len(files), "files": files, "truncated": len(files) >= args.max_files}


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


class ProjectTreeTool(BaseTool):
    name = "project_tree"
    description = "Return a compact directory tree for a project, ignoring dependencies and build artifacts."
    args_schema = ProjectTreeArgs

    def run(self, **kwargs: Any) -> dict[str, Any]:
        args = self.validate_args(kwargs)
        assert isinstance(args, ProjectTreeArgs)
        root = _resolve_existing_dir(args.project_path)
        entries: list[str] = []

        for path in iter_project_paths(root):
            relative = path.relative_to(root)
            depth = len(relative.parts)
            if depth > args.max_depth:
                continue
            marker = "/" if path.is_dir() else ""
            entries.append(f"{'  ' * (depth - 1)}{relative.name}{marker}")
            if len(entries) >= args.max_entries:
                break

        return {
            "project_path": str(root),
            "max_depth": args.max_depth,
            "count": len(entries),
            "entries": entries,
            "truncated": len(entries) >= args.max_entries,
        }


class FindFilesTool(BaseTool):
    name = "find_files"
    description = "Find files by case-insensitive name substring or glob-like pattern under a project path."
    args_schema = FindFilesArgs

    def run(self, **kwargs: Any) -> dict[str, Any]:
        args = self.validate_args(kwargs)
        assert isinstance(args, FindFilesArgs)
        root = _resolve_existing_dir(args.project_path)
        pattern = args.pattern.lower()
        matches: list[str] = []

        for path in iter_project_paths(root):
            if not path.is_file():
                continue
            relative = path.relative_to(root).as_posix()
            if pattern in relative.lower() or path.match(args.pattern):
                matches.append(relative)
                if len(matches) >= args.max_results:
                    break

        return {
            "project_path": str(root),
            "pattern": args.pattern,
            "count": len(matches),
            "matches": matches,
            "truncated": len(matches) >= args.max_results,
        }


def iter_project_paths(root: Path) -> Iterator[Path]:
    """Yield project paths in a stable order without descending ignored dirs.

    The tools use this generator instead of `Path.rglob()` so dependency
    folders are pruned before recursion. That keeps list/search/tree operations
    responsive on real codebases with large `node_modules`, virtualenvs, or
    build outputs.
    """

    try:
        children = sorted(root.iterdir(), key=lambda item: (item.is_file(), item.name.lower()))
    except OSError:
        return

    for child in children:
        if child.name in IGNORED_DIRS:
            continue
        yield child
        if child.is_dir():
            yield from iter_project_paths(child)
