from fastapi import APIRouter, Depends

from app.api.schemas import (
    ProjectIndexRequest,
    ProjectIndexResponse,
    ProjectSearchRequest,
    ProjectSearchResponse,
    ProjectSearchResult,
)
from app.core.logger import get_logger
from app.core.project_paths import normalize_project_path
from app.rag.embeddings import LocalHashEmbeddingClient
from app.rag.retriever import CodeRetriever

router = APIRouter(prefix="/api/projects", tags=["projects"])
logger = get_logger(__name__)


def get_retriever() -> CodeRetriever:
    """Provide the project retriever used by indexing and search endpoints."""

    return CodeRetriever(embedding_client=LocalHashEmbeddingClient())


@router.post("/index", response_model=ProjectIndexResponse)
def index_project(
    request: ProjectIndexRequest,
    retriever: CodeRetriever = Depends(get_retriever),
) -> ProjectIndexResponse:
    """Build or refresh the code retrieval index for a local project path."""

    project_path = normalize_project_path(request.project_path)
    logger.info("Project index request received project_path=%s normalized_project_path=%s", request.project_path, project_path)
    stats = retriever.index_project(project_path)
    logger.info(
        "Project index completed project_path=%s indexed_files=%s chunks=%s",
        project_path,
        stats["indexed_files"],
        stats["chunks"],
    )
    return ProjectIndexResponse(indexed_files=stats["indexed_files"], chunks=stats["chunks"])


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
