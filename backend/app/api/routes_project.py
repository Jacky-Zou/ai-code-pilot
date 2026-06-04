from pathlib import Path

from fastapi import APIRouter, Depends

from app.api.schemas import (
    ProjectLanguageSummary,
    ProjectIndexRequest,
    ProjectIndexResponse,
    ProjectSearchRequest,
    ProjectSearchResponse,
    ProjectSearchResult,
)
from app.core.logger import get_logger
from app.core.project_paths import normalize_project_path
from app.rag.embeddings import LocalHashEmbeddingClient
from app.rag.indexer import ProjectFile, ProjectIndexer
from app.rag.retriever import CodeRetriever

router = APIRouter(prefix="/api/projects", tags=["projects"])
logger = get_logger(__name__)

LANGUAGE_BY_EXTENSION = {
    ".py": "Python",
    ".pyi": "Python",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".java": "Java",
    ".go": "Go",
    ".rs": "Rust",
    ".c": "C/C++",
    ".h": "C/C++",
    ".cpp": "C/C++",
    ".hpp": "C/C++",
    ".cs": "C#",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "CSS",
    ".json": "Config",
    ".yaml": "Config",
    ".yml": "Config",
    ".toml": "Config",
    ".md": "Markdown",
}


def get_retriever() -> CodeRetriever:
    """Provide the project retriever used by indexing and search endpoints."""

    return CodeRetriever(embedding_client=LocalHashEmbeddingClient())


def _language_for_file(relative_path: str) -> str:
    """Return a compact language label for project overview metrics."""

    path = Path(relative_path)
    if path.name in {"Dockerfile", "Makefile"}:
        return path.name
    return LANGUAGE_BY_EXTENSION.get(path.suffix.lower(), "Other")


def _detect_tech_stack(files: list[ProjectFile]) -> list[str]:
    """Infer a practical tech-stack summary from canonical project files."""

    names = {Path(project_file.relative_path).name.lower() for project_file in files}
    paths = {project_file.relative_path.lower() for project_file in files}
    stack: list[str] = []
    if "requirements.txt" in names or "pyproject.toml" in names:
        stack.append("Python")
    if any(path.endswith("app/main.py") for path in paths) or any("fastapi" in path for path in paths):
        stack.append("FastAPI")
    if "package.json" in names:
        stack.append("Node.js")
    if any(path.endswith((".tsx", ".jsx")) for path in paths):
        stack.append("React")
    if any(path.startswith("frontend/app/") or "next.config" in path for path in paths):
        stack.append("Next.js")
    if any("tailwind" in path for path in paths):
        stack.append("Tailwind CSS")
    if "docker-compose.yml" in names or "dockerfile" in names:
        stack.append("Docker")
    if any("rag/" in path for path in paths):
        stack.append("RAG")
    if any("agent/" in path for path in paths):
        stack.append("LLM Agent")
    return list(dict.fromkeys(stack))[:10] or ["Text/code project"]


def _detect_architecture(files: list[ProjectFile]) -> list[str]:
    """Infer high-level architecture areas from folder ownership."""

    top_parts = {project_file.relative_path.split("/", 1)[0] for project_file in files}
    paths = {project_file.relative_path.lower() for project_file in files}
    architecture: list[str] = []
    if "backend" in top_parts:
        architecture.append("Backend service layer")
    if "frontend" in top_parts:
        architecture.append("Frontend workspace application")
    if any("agent/" in path for path in paths):
        architecture.append("Agent planner/executor core")
    if any("tools/" in path for path in paths):
        architecture.append("Tool calling layer")
    if any("rag/" in path for path in paths):
        architecture.append("RAG indexing and retrieval layer")
    if "docs" in top_parts:
        architecture.append("Documentation package")
    if "tests" in top_parts or any("/tests/" in path for path in paths):
        architecture.append("Automated test suite")
    return architecture[:8] or ["Single-project codebase"]


def _summarize_project(
    project_path: str,
    files: list[ProjectFile],
    indexed_file_count: int,
    chunks: int,
) -> ProjectIndexResponse:
    """Build the project overview returned to the frontend summary modal.

    The RAG index is useful for search, but users also need immediate
    orientation after import. This deterministic summary keeps the modal fast,
    testable, and independent from an additional model call.
    """

    root = Path(project_path)
    language_counts: dict[str, int] = {}
    structure_counts: dict[str, int] = {}
    line_count = 0
    size_bytes = 0

    for project_file in files:
        language = _language_for_file(project_file.relative_path)
        language_counts[language] = language_counts.get(language, 0) + 1
        size_bytes += project_file.size
        parts = project_file.relative_path.split("/")
        if len(parts) > 1:
            structure_counts[parts[0]] = structure_counts.get(parts[0], 0) + 1
        try:
            line_count += len(project_file.path.read_text(encoding="utf-8").splitlines())
        except UnicodeDecodeError:
            continue

    total_files = len(files) or 1
    languages = [
        ProjectLanguageSummary(label=label, files=count, percent=round((count / total_files) * 100))
        for label, count in sorted(language_counts.items(), key=lambda item: item[1], reverse=True)
    ][:8]
    structure = [
        f"{folder}/ ({count} files)" for folder, count in sorted(structure_counts.items(), key=lambda item: item[1], reverse=True)
    ][:10]
    tech_stack = _detect_tech_stack(files)
    architecture = _detect_architecture(files)
    project_name = root.name or "Workspace"

    likely_purpose = (
        "This project appears to be organized for codebase analysis, development assistance, API services, and documentation workflows."
        if {"LLM Agent", "RAG"} & set(tech_stack)
        else "This project appears to be a software codebase prepared for inspection, search, and development support."
    )

    return ProjectIndexResponse(
        indexed_files=indexed_file_count,
        chunks=chunks,
        project_name=project_name,
        project_path=str(root),
        size_bytes=size_bytes,
        line_count=line_count,
        languages=languages,
        tech_stack=tech_stack,
        architecture=architecture,
        structure=structure,
        summary=f"{project_name} contains {indexed_file_count} indexed source/documentation files and {chunks} retrieval chunks.",
        likely_purpose=likely_purpose,
    )


@router.post("/index", response_model=ProjectIndexResponse)
def index_project(
    request: ProjectIndexRequest,
    retriever: CodeRetriever = Depends(get_retriever),
) -> ProjectIndexResponse:
    """Build or refresh the code retrieval index for a local project path."""

    project_path = normalize_project_path(request.project_path)
    logger.info("Project index request received project_path=%s normalized_project_path=%s", request.project_path, project_path)
    indexed_files = ProjectIndexer().scan_files(project_path)
    stats = retriever.index_project(project_path)
    logger.info(
        "Project index completed project_path=%s indexed_files=%s chunks=%s",
        project_path,
        stats["indexed_files"],
        stats["chunks"],
    )
    return _summarize_project(
        project_path=project_path,
        files=indexed_files,
        indexed_file_count=stats["indexed_files"],
        chunks=stats["chunks"],
    )


@router.post("/search", response_model=ProjectSearchResponse)
def search_project(
    request: ProjectSearchRequest,
    retriever: CodeRetriever = Depends(get_retriever),
) -> ProjectSearchResponse:
    """Search the current project retrieval index and expose API result models."""

    logger.info("Project search request received top_k=%s", request.top_k)
    chunks = retriever.search(query=request.query, top_k=request.top_k)
    logger.info("Project search completed top_k=%s results=%s", request.top_k, len(chunks))
    return ProjectSearchResponse(
        results=[
            ProjectSearchResult(
                file_path=chunk.file_path,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                content=chunk.content,
                score=chunk.score,
            )
            for chunk in chunks
        ]
    )
