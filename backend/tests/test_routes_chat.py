from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.agent.schemas import AgentResponse, CodeReference, ToolResult
from app.api.routes_chat import get_agent, router


class FakeAgent:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def run(
        self,
        message: str,
        project_path: str | None = None,
        provider: str | None = None,
        model: str | None = None,
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
            answer="Found the chat router.",
            provider=provider or "openai",
            model=model or "gpt-5.2",
            tool_calls=[
                ToolResult(
                    name="search_text",
                    arguments={"keyword": "chat"},
                    result={"matches": []},
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


def create_test_client(fake_agent: FakeAgent) -> TestClient:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_agent] = lambda: fake_agent
    return TestClient(app)


def test_chat_route_passes_request_to_agent(tmp_path) -> None:
    fake_agent = FakeAgent()
    client = create_test_client(fake_agent)

    response = client.post(
        "/api/chat",
        json={
            "message": "Where is chat implemented?",
            "project_path": str(tmp_path),
            "provider": "deepseek",
            "model": "deepseek-v4-pro",
        },
    )

    assert response.status_code == 200
    assert fake_agent.calls == [
        {
            "message": "Where is chat implemented?",
            "project_path": str(tmp_path.resolve()),
            "provider": "deepseek",
            "model": "deepseek-v4-pro",
        }
    ]


def test_chat_route_returns_agent_response_shape() -> None:
    fake_agent = FakeAgent()
    client = create_test_client(fake_agent)

    response = client.post("/api/chat", json={"message": "Find chat router"})

    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "Found the chat router."
    assert data["provider"] == "openai"
    assert data["model"] == "gpt-5.2"
    assert data["tool_calls"][0]["name"] == "search_text"
    assert data["references"][0]["file_path"] == "backend/app/api/routes_chat.py"
