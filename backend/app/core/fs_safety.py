"""Shared filesystem safety utilities.

Centralises path-resolution logic that must be used across multiple tool
modules (file_tools, search_tools, rag_tools, patch_tools). Keeping it here
avoids cross-module imports of private `_`-prefixed functions.
"""

from pathlib import Path

from app.core.exceptions import ToolError
from app.core.project_paths import normalize_project_path


def resolve_existing_dir(path: str) -> Path:
    """Resolve a project directory, raising ToolError if missing or not a dir."""
    root = Path(normalize_project_path(path)).expanduser().resolve()
    if not root.exists():
        raise ToolError(f"Project path does not exist: {path}")
    if not root.is_dir():
        raise ToolError(f"Project path is not a directory: {path}")
    return root


def resolve_file(file_path: str, project_path: str | None) -> tuple[Path, Path]:
    """Resolve a file path confined to the project root.

    Returns (root, resolved_absolute_path). Raises ToolError when the file
    does not exist, is not a file, or escapes the project root (path traversal).
    """
    if project_path:
        root = resolve_existing_dir(project_path)
        candidate = Path(file_path).expanduser()
        resolved = (root / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()
    else:
        resolved = Path(file_path).expanduser().resolve()
        root = resolved.parent

    if not resolved.exists():
        raise ToolError(f"File does not exist: {file_path}")
    if not resolved.is_file():
        raise ToolError(f"Path is not a file: {file_path}")
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ToolError("File path is outside the allowed project root") from exc
    return root, resolved
