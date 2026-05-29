import pytest
from pydantic import ValidationError

from app.api.schemas import (
    ChatRequest,
    ChatResponse,
    ErrorResponse,
    HealthResponse,
    ProjectIndexRequest,
    ProjectIndexResponse,
    ProjectSearchRequest,
    ProjectSearchResponse,
    ProjectSearchResult,
)


def test_health_response_defaults() -> None:
    response = HealthResponse()

    assert response.status == "ok"
    assert response.service == "AICodePilot"


def test_chat_request_supports_dynamic_provider_and_model() -> None:
    request = ChatRequest(
        message="Analyze this project",
        project_path="/tmp/project",
        provider="deepseek",
        model="deepseek-v4-pro",
    )

    assert request.provider == "deepseek"
    assert request.model == "deepseek-v4-pro"


def test_chat_request_requires_message() -> None:
    with pytest.raises(ValidationError):
        ChatRequest(message="")


def test_chat_response_defaults_lists() -> None:
    response = ChatResponse(answer="ok", provider="openai", model="gpt-5.2")

    assert response.tool_calls == []
    assert response.references == []


def test_project_index_schema() -> None:
    request = ProjectIndexRequest(project_path="/tmp/project")
    response = ProjectIndexResponse(indexed_files=3, chunks=8)

    assert request.project_path == "/tmp/project"
    assert response.status == "success"
    assert response.indexed_files == 3
    assert response.chunks == 8


def test_project_search_schema_validates_top_k() -> None:
    with pytest.raises(ValidationError):
        ProjectSearchRequest(query="agent", top_k=0)

    request = ProjectSearchRequest(query="agent", top_k=5)
    assert request.top_k == 5


def test_project_search_response_contains_results() -> None:
    result = ProjectSearchResult(
        file_path="backend/app/agent/executor.py",
        start_line=1,
        end_line=10,
        content="class AgentExecutor",
        score=0.9,
    )
    response = ProjectSearchResponse(results=[result])

    assert response.results[0].file_path.endswith("executor.py")


def test_error_response_schema() -> None:
    response = ErrorResponse(
        error="ConfigurationError",
        code="CONFIGURATION_ERROR",
        detail="missing key",
        request_id="req-123",
    )

    assert response.error == "ConfigurationError"
    assert response.code == "CONFIGURATION_ERROR"
    assert response.detail == "missing key"
    assert response.request_id == "req-123"
