from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from app.agent.schemas import AgentResponse, CodeReference, ToolResult
from app.api.routes_chat import get_agent
from app.api.routes_project import get_retriever
from app.main import create_app
from app.rag.schemas import RetrievedChunk


class FakeAgent:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def run(
        self,
        message: str,
        project_path: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        **_: object,
    ) -> AgentResponse:
        self.calls.append(
            {
                "message": message,
                "project_path": project_path,
                "provider": provider,
                "model": model,
            }
        )
        return AgentResponse(
            answer="The API router is wired correctly.",
            provider=provider or "openai",
            model=model or "gpt-5.2",
            tool_calls=[
                ToolResult(
                    name="search_text",
                    arguments={"keyword": "router"},
                    result={"matches": 1},
                )
            ],
            references=[
                CodeReference(
                    file_path="backend/app/api/routes_chat.py",
                    line_number=1,
                    snippet="router = APIRouter",
                )
            ],
        )


class FakeRetriever:
    def __init__(self) -> None:
        self.index_calls: list[str] = []
        self.search_calls: list[dict[str, Any]] = []

    def index_project(self, project_path: str | Path) -> dict[str, int]:
        self.index_calls.append(str(project_path))
        return {"indexed_files": 2, "chunks": 5}

    def search(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        self.search_calls.append({"query": query, "top_k": top_k})
        return [
            RetrievedChunk(
                file_path="backend/app/main.py",
                start_line=8,
                end_line=20,
                content="app = create_app()",
                score=0.88,
            )
        ]


def create_test_client(fake_agent: FakeAgent, fake_retriever: FakeRetriever) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_agent] = lambda: fake_agent
    app.dependency_overrides[get_retriever] = lambda: fake_retriever
    return TestClient(app)


def test_health_endpoint_returns_service_status() -> None:
    client = create_test_client(FakeAgent(), FakeRetriever())

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "AICodePilot"}


def test_chat_endpoint_returns_agent_answer_and_metadata(tmp_path: Path) -> None:
    fake_agent = FakeAgent()
    client = create_test_client(fake_agent, FakeRetriever())

    response = client.post(
        "/api/chat",
        json={
            "message": "Where is the API router?",
            "project_path": str(tmp_path),
            "provider": "deepseek",
            "model": "deepseek-chat",
        },
    )

    assert response.status_code == 200
    assert fake_agent.calls == [
        {
            "message": "Where is the API router?",
            "project_path": str(tmp_path.resolve()),
            "provider": "deepseek",
            "model": "deepseek-chat",
        }
    ]
    data = response.json()
    assert data["answer"] == "The API router is wired correctly."
    assert data["provider"] == "deepseek"
    assert data["model"] == "deepseek-chat"
    assert data["tool_calls"][0]["name"] == "search_text"
    assert data["references"][0]["file_path"] == "backend/app/api/routes_chat.py"


def test_project_index_endpoint_returns_indexing_stats(tmp_path: Path) -> None:
    fake_retriever = FakeRetriever()
    client = create_test_client(FakeAgent(), fake_retriever)

    response = client.post("/api/projects/index", json={"project_path": str(tmp_path)})

    assert response.status_code == 200
    assert fake_retriever.index_calls == [str(tmp_path.resolve())]
    data = response.json()
    assert data["status"] == "success"
    assert data["indexed_files"] == 2
    assert data["chunks"] == 5
    assert data["project_name"] == tmp_path.name
    assert "size_bytes" in data
    assert "line_count" in data
    assert "tech_stack" in data
    assert "architecture" in data
    assert data["summary"]


def test_project_search_endpoint_returns_code_results() -> None:
    fake_retriever = FakeRetriever()
    client = create_test_client(FakeAgent(), fake_retriever)

    response = client.post("/api/projects/search", json={"query": "main app", "top_k": 3})

    assert response.status_code == 200
    assert fake_retriever.search_calls == [{"query": "main app", "top_k": 3}]
    assert response.json() == {
        "results": [
            {
                "file_path": "backend/app/main.py",
                "start_line": 8,
                "end_line": 20,
                "content": "app = create_app()",
                "score": 0.88,
            }
        ]
    }


def test_api_validation_errors_use_unified_error_shape() -> None:
    client = create_test_client(FakeAgent(), FakeRetriever())

    response = client.post("/api/chat", json={"message": ""})

    assert response.status_code == 422
    data = response.json()
    assert data["error"] == "ValidationError"
    assert isinstance(data["detail"], list)
