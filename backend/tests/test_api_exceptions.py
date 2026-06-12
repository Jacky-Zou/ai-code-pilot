from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes_chat import get_agent
from app.core.exceptions import ConfigurationError, LLMProviderError, ToolError, register_exception_handlers
from app.main import create_app


class FailingAgent:
    def run(
        self,
        message: str,
        project_path: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        **_: object,
    ) -> object:
        raise ConfigurationError("OPENAI_API_KEY is required")


def test_domain_errors_return_consistent_error_response() -> None:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/boom")
    def boom() -> None:
        raise ToolError("Project path is outside the allowed root")

    response = TestClient(app).get("/boom")

    assert response.status_code == 400
    assert response.json() == {
        "error": "ToolError",
        "code": "TOOL_ERROR",
        "detail": "Project path is outside the allowed root",
    }


def test_configuration_errors_return_server_error_response() -> None:
    app = create_app()
    app.dependency_overrides[get_agent] = lambda: FailingAgent()

    response = TestClient(app).post("/api/chat", json={"message": "hello"})

    assert response.status_code == 500
    assert response.json() == {
        "error": "ConfigurationError",
        "code": "CONFIGURATION_ERROR",
        "detail": "OPENAI_API_KEY is required",
    }


def test_request_validation_errors_return_consistent_error_response() -> None:
    response = TestClient(create_app()).post("/api/chat", json={"message": ""})

    assert response.status_code == 422
    data = response.json()
    assert data["error"] == "ValidationError"
    assert data["code"] == "VALIDATION_ERROR"
    assert isinstance(data["detail"], list)
    assert data["detail"][0]["loc"] == ["body", "message"]


def test_domain_errors_include_request_id_when_header_is_present() -> None:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/provider-error")
    def provider_error() -> None:
        raise LLMProviderError("LLM provider returned HTTP 500")

    response = TestClient(app).get("/provider-error", headers={"X-Request-ID": "req-123"})

    assert response.status_code == 502
    assert response.json() == {
        "error": "LLMProviderError",
        "code": "LLM_PROVIDER_ERROR",
        "detail": "LLM provider returned HTTP 500",
        "request_id": "req-123",
    }
