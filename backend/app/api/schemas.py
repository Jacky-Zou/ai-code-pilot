from typing import Any, Literal

from pydantic import BaseModel, Field

from app.agent.schemas import CodeReference, ToolResult


class HealthResponse(BaseModel):
    """Response returned by the service health endpoint."""

    status: Literal["ok"] = "ok"
    service: str = "AICodePilot"


class ChatRequest(BaseModel):
    """HTTP request body for asking the Agent a codebase question.

    `provider` and `model` are optional by design. When omitted, the backend
    resolves them from environment configuration, preserving the dynamic model
    selection rules established in Phase 1.
    """

    message: str = Field(min_length=1)
    project_path: str | None = None
    provider: str | None = None
    model: str | None = None


class ChatResponse(BaseModel):
    """HTTP response body for Agent answers.

    The shape mirrors `AgentResponse` so API clients can render the final answer,
    model choice, executed tools, and code references without knowing internal
    Agent classes.
    """

    answer: str
    provider: str
    model: str
    tool_calls: list[ToolResult] = Field(default_factory=list)
    references: list[CodeReference] = Field(default_factory=list)


class ProjectIndexRequest(BaseModel):
    """Request body for building a RAG index for a local project path."""

    project_path: str = Field(min_length=1)


class ProjectLanguageSummary(BaseModel):
    """Language distribution entry for an indexed project."""

    label: str
    files: int = Field(ge=0)
    percent: int = Field(ge=0, le=100)


class ProjectIndexResponse(BaseModel):
    """Summary returned after indexing a project for retrieval."""

    status: Literal["success"] = "success"
    indexed_files: int = Field(ge=0)
    chunks: int = Field(ge=0)
    project_name: str = ""
    project_path: str = ""
    size_bytes: int = Field(default=0, ge=0)
    line_count: int = Field(default=0, ge=0)
    languages: list[ProjectLanguageSummary] = Field(default_factory=list)
    tech_stack: list[str] = Field(default_factory=list)
    architecture: list[str] = Field(default_factory=list)
    structure: list[str] = Field(default_factory=list)
    summary: str = ""
    likely_purpose: str = ""


class ProjectSearchRequest(BaseModel):
    """Request body for searching the current project vector index."""

    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class ProjectSearchResult(BaseModel):
    """One code snippet returned by project semantic search."""

    file_path: str
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    content: str
    score: float


class ProjectSearchResponse(BaseModel):
    """Response body for project semantic search."""

    results: list[ProjectSearchResult] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    """Consistent API error response returned by registered exception handlers."""

    error: str
    code: str | None = None
    detail: str | dict[str, Any] | list[dict[str, Any]] | None = None
    request_id: str | None = None
