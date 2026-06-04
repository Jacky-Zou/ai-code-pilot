from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes_project import get_retriever, router
from app.rag.schemas import RetrievedChunk


class FakeRetriever:
    def __init__(self) -> None:
        self.index_calls: list[str] = []
        self.search_calls: list[dict[str, object]] = []

    def index_project(self, project_path: str | Path) -> dict[str, int]:
        self.index_calls.append(str(project_path))
        return {"indexed_files": 3, "chunks": 7}

    def search(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        self.search_calls.append({"query": query, "top_k": top_k})
        return [
            RetrievedChunk(
                file_path="backend/app/api/routes_project.py",
                start_line=1,
                end_line=20,
                content="router = APIRouter",
                score=0.92,
            )
        ]


def create_test_client(fake_retriever: FakeRetriever) -> TestClient:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_retriever] = lambda: fake_retriever
    return TestClient(app)


def test_project_index_route_calls_retriever(tmp_path: Path) -> None:
    fake_retriever = FakeRetriever()
    client = create_test_client(fake_retriever)

    response = client.post("/api/projects/index", json={"project_path": str(tmp_path)})

    assert response.status_code == 200
    assert fake_retriever.index_calls == [str(tmp_path.resolve())]
    data = response.json()
    assert data["status"] == "success"
    assert data["indexed_files"] == 3
    assert data["chunks"] == 7
    assert data["project_name"] == tmp_path.name
    assert data["size_bytes"] == 0
    assert data["line_count"] == 0
    assert data["languages"] == []
    assert data["summary"]


def test_project_search_route_returns_retrieved_chunks() -> None:
    fake_retriever = FakeRetriever()
    client = create_test_client(fake_retriever)

    response = client.post("/api/projects/search", json={"query": "project router", "top_k": 2})

    assert response.status_code == 200
    assert fake_retriever.search_calls == [{"query": "project router", "top_k": 2}]
    data = response.json()
    assert data["results"][0]["file_path"] == "backend/app/api/routes_project.py"
    assert data["results"][0]["start_line"] == 1
    assert data["results"][0]["score"] == 0.92
