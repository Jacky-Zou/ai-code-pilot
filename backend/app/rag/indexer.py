from pathlib import Path

from pydantic import BaseModel, Field

from app.core.exceptions import ToolError

IGNORED_DIRECTORIES = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    "tests",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".next",
    "out",
    "chroma",
    "faiss_index",
    "tmp",
    "temp",
}

CODE_TEXT_EXTENSIONS = {
    ".py",
    ".pyi",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".java",
    ".go",
    ".rs",
    ".c",
    ".h",
    ".cpp",
    ".hpp",
    ".cs",
    ".php",
    ".rb",
    ".swift",
    ".kt",
    ".scala",
    ".sh",
    ".ps1",
    ".sql",
    ".html",
    ".css",
    ".scss",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".md",
    ".txt",
    ".env.example",
    ".gitignore",
    "",
}

MAX_SCAN_FILE_BYTES = 2_000_000


class ProjectFile(BaseModel):
    """A text/code file discovered under a project root."""

    path: Path
    relative_path: str
    size: int = Field(ge=0)


class ProjectIndexer:
    """Scan a local project and return files that are useful for code RAG.

    The indexer is intentionally conservative: it skips known dependency,
    cache, build, and VCS directories before touching file contents. For files
    that pass the directory and extension checks, it reads a small byte sample
    to reject binary payloads without loading large files into memory.
    """

    def __init__(
        self,
        ignored_directories: set[str] | None = None,
        max_file_bytes: int = MAX_SCAN_FILE_BYTES,
    ) -> None:
        self.ignored_directories = ignored_directories or IGNORED_DIRECTORIES
        self.max_file_bytes = max_file_bytes

    def scan_files(self, project_path: str | Path) -> list[ProjectFile]:
        root = Path(project_path).expanduser().resolve()
        if not root.exists():
            raise ToolError(f"Project path does not exist: {project_path}")
        if not root.is_dir():
            raise ToolError(f"Project path is not a directory: {project_path}")

        files: list[ProjectFile] = []
        for path in sorted(root.rglob("*")):
            if self._should_skip_path(path, root):
                continue
            if not path.is_file():
                continue
            size = path.stat().st_size
            if size > self.max_file_bytes:
                continue
            if not self._has_text_extension(path):
                continue
            if self._looks_binary(path):
                continue
            files.append(ProjectFile(path=path, relative_path=path.relative_to(root).as_posix(), size=size))
        return files

    def _should_skip_path(self, path: Path, root: Path) -> bool:
        relative_parts = path.relative_to(root).parts
        return any(part in self.ignored_directories for part in relative_parts)

    def _has_text_extension(self, path: Path) -> bool:
        if path.name in {"Dockerfile", "Makefile", "LICENSE"}:
            return True
        return path.suffix.lower() in CODE_TEXT_EXTENSIONS

    def _looks_binary(self, path: Path) -> bool:
        sample = path.read_bytes()[:4096]
        if b"\x00" in sample:
            return True
        try:
            sample.decode("utf-8")
        except UnicodeDecodeError:
            return True
        return False
