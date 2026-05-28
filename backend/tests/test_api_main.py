from fastapi.testclient import TestClient

from app.agent.schemas import AgentResponse
from app.api.routes_chat import get_agent
from app.api.routes_project import get_retriever
from app.main import app, create_app
from app.rag.schemas import RetrievedChunk


class FakeAgent:
    def run(
        self,
        message: str,
        project_path: str | None = None,
        provider: str | None = None,
        model: str | None = None,
    ) -> AgentResponse:
        return AgentResponse(
            answer=f"Echo: {message}",
            provider=provider or "openai",
            model=model or "gpt-5.2",
        )


class FakeRetriever:
    def index_project(self, project_path: str) -> dict[str, int]:
        return {"indexed_files": 1, "chunks": 2}

    def search(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        return [
            RetrievedChunk(
                file_path="backend/app/main.py",
                start_line=1,
                end_line=10,
                content="app = create_app()",
                score=0.9,
            )
        ]


def test_create_app_exposes_health_endpoint() -> None:
    client = TestClient(create_app())

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "AICodePilot"}


def test_main_app_exposes_openapi_schema() -> None:
    client = TestClient(app)

    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/health" in paths
    assert "/api/chat" in paths
    assert "/api/projects/index" in paths
    assert "/api/projects/search" in paths


def test_main_app_wires_phase_three_routers() -> None:
    test_app = create_app()
    test_app.dependency_overrides[get_agent] = lambda: FakeAgent()
    test_app.dependency_overrides[get_retriever] = lambda: FakeRetriever()
    client = TestClient(test_app)

    chat_response = client.post("/api/chat", json={"message": "hello"})
    index_response = client.post("/api/projects/index", json={"project_path": "/tmp/project"})
    search_response = client.post("/api/projects/search", json={"query": "main app"})

    assert chat_response.status_code == 200
    assert chat_response.json()["answer"] == "Echo: hello"
    assert index_response.status_code == 200
    assert index_response.json()["chunks"] == 2
    assert search_response.status_code == 200
    assert search_response.json()["results"][0]["file_path"] == "backend/app/main.py"
