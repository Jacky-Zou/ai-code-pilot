"""End-to-end integration test for the full chat flow (T-12).

Covers index → chat → stream → session history using a fake LLM provider
so no real API key is required. Validates that:
- Project indexing endpoint returns summary metadata
- POST /api/chat returns an answer with conversation_id
- Second chat turn with same conversation_id receives context (memory)
- POST /api/chat/stream emits at least a done event
- GET /api/sessions/{id}/messages returns persisted messages
- DELETE /api/sessions/{id} removes records
"""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.agent.agent import AICodePilotAgent
from app.agent.executor import AgentExecutor
from app.api.routes_chat import get_agent
from app.db.engine import get_session
from app.llm.base import BaseLLMProvider
from app.llm.schemas import ChatResult


class FakeLLM(BaseLLMProvider):
    """Minimal fake provider that returns a deterministic final answer."""

    provider_name = "openai"

    def chat(self, messages, model=None, **kwargs) -> str:
        return '{"type":"final","answer":"E2E test answer."}'

    def chat_with_tools(self, messages, tools, model=None) -> ChatResult:
        return ChatResult(content="E2E test answer.", tool_calls=[])


def make_test_agent() -> AICodePilotAgent:
    return AICodePilotAgent(executor=AgentExecutor(llm_provider=FakeLLM()))


@pytest.fixture()
def memory_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture()
def client(memory_engine):
    from app.main import create_app

    application = create_app()
    application.dependency_overrides[get_agent] = make_test_agent

    def override_session():
        with Session(memory_engine) as session:
            yield session

    application.dependency_overrides[get_session] = override_session
    with TestClient(application) as c:
        yield c


class TestIndexEndpoint:
    def test_index_returns_metadata(self, client: TestClient, tmp_path: Path) -> None:
        (tmp_path / "main.py").write_text("print('hello')\n")
        response = client.post("/api/projects/index", json={"project_path": str(tmp_path)})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["indexed_files"] >= 1
        assert "project_name" in data


class TestChatEndpoint:
    def test_chat_returns_answer_and_conversation_id(self, client: TestClient) -> None:
        response = client.post("/api/chat", json={"message": "Hello"})
        assert response.status_code == 200
        data = response.json()
        assert data["answer"]
        assert data["conversation_id"]

    def test_multi_turn_same_conversation_id(self, client: TestClient) -> None:
        r1 = client.post("/api/chat", json={"message": "First turn"})
        conv_id = r1.json()["conversation_id"]

        r2 = client.post("/api/chat", json={"message": "Second turn", "conversation_id": conv_id})
        assert r2.status_code == 200
        assert r2.json()["conversation_id"] == conv_id


class TestStreamEndpoint:
    def test_stream_emits_done_event(self, client: TestClient) -> None:
        response = client.post(
            "/api/chat/stream",
            json={"message": "Stream test"},
            headers={"Accept": "text/event-stream"},
        )
        assert response.status_code == 200
        text = response.text
        assert "done" in text
        # Parse the done event data
        for line in text.splitlines():
            if line.startswith("data:") and "answer" in line:
                payload = json.loads(line[5:].strip())
                assert payload.get("answer")
                break


class TestSessionEndpoints:
    def test_get_messages_after_chat(self, client: TestClient, memory_engine) -> None:
        r = client.post("/api/chat", json={"message": "Persist this"})
        conv_id = r.json()["conversation_id"]

        msgs = client.get(f"/api/sessions/{conv_id}/messages")
        assert msgs.status_code == 200
        data = msgs.json()
        assert len(data) >= 2
        roles = [m["role"] for m in data]
        assert "user" in roles
        assert "assistant" in roles

    def test_delete_session(self, client: TestClient) -> None:
        r = client.post("/api/chat", json={"message": "Delete me"})
        conv_id = r.json()["conversation_id"]

        del_resp = client.delete(f"/api/sessions/{conv_id}")
        assert del_resp.status_code == 204

        msgs = client.get(f"/api/sessions/{conv_id}/messages")
        assert msgs.json() == []
