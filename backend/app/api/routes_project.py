from fastapi import APIRouter, Depends

from app.api.schemas import (
    ProjectIndexRequest,
    ProjectIndexResponse,
    ProjectSearchRequest,
    ProjectSearchResponse,
    ProjectSearchResult,
)
from app.rag.embeddings import LocalHashEmbeddingClient
from app.rag.retriever import CodeRetriever

router = APIRouter(prefix="/api/projects", tags=["projects"])


def get_retriever() -> CodeRetriever:
    """Provide the project retriever used by indexing and search endpoints."""

    return CodeRetriever(embedding_client=LocalHashEmbeddingClient())


@router.post("/index", response_model=ProjectIndexResponse)
def index_project(
    request: ProjectIndexRequest,
    retriever: CodeRetriever = Depends(get_retriever),
) -> ProjectIndexResponse:
    """Build or refresh the code retrieval index for a local project path."""

    stats = retriever.index_project(request.project_path)
    return ProjectIndexResponse(indexed_files=stats["indexed_files"], chunks=stats["chunks"])


@router.post("/search", response_model=ProjectSearchResponse)
def search_project(
    request: ProjectSearchRequest,
    retriever: CodeRetriever = Depends(get_retriever),
) -> ProjectSearchResponse:
    """Search the current project retrieval index and expose API result models."""

    chunks = retriever.search(query=request.query, top_k=request.top_k)
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
