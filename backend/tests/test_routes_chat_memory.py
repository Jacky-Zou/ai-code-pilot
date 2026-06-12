"""Integration tests: multi-turn memory wired through routes_chat.

Verifies that consecutive POST /api/chat requests with the same conversation_id
cause the second request's provider call to include the first turn in history.

T-1 requirement: ConversationMemory is truly connected to the main flow.
"""

from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import create_app

# ---------------------------------------------------------------------------
# Fake LLM provider: records all messages it receives and returns a simple answer.
# ---------------------------------------------------------------------------


class FakeLLMProvider:
    provider_name = "openai"

    def __init__(self) -> None:
        self.call_history: list[list[dict[str, Any]]] = []

    def chat(
        self,
        messages: list[dict[str, Any]],
        model: str | None = None,
        **kwargs: Any,
    ) -> str:
        self.call_history.append(list(messages))
        return '{"type":"final","answer":"fake answer"}'

    def chat_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        model: str | None = None,
    ) -> Any:
        # Delegate to chat for simplicity in memory tests
        from app.llm.schemas import ChatResult

        self.call_history.append(list(messages))
        return ChatResult(content="fake answer", tool_calls=[])


@pytest.fixture()
def client_with_fake_provider() -> tuple[TestClient, FakeLLMProvider]:
    fake = FakeLLMProvider()

    app = create_app()
    client = TestClient(app, raise_server_exceptions=True)

    with patch("app.llm.factory.LLMProviderFactory.create", return_value=fake):
        yield client, fake  # type: ignore[misc]


def test_second_request_receives_first_turn_in_history(
    client_with_fake_provider: tuple[TestClient, FakeLLMProvider],
) -> None:
    """The second call must contain the first Q&A turn in provider messages."""

    client, fake = client_with_fake_provider

    # First request — no conversation_id, server will mint one
    resp1 = client.post(
        "/api/chat",
        json={"message": "What is the project structure?"},
    )
    assert resp1.status_code == 200
    body1 = resp1.json()
    conv_id = body1["conversation_id"]
    assert conv_id  # server always returns one

    # Second request — same conversation_id
    resp2 = client.post(
        "/api/chat",
        json={"message": "Now explain the executor module.", "conversation_id": conv_id},
    )
    assert resp2.status_code == 200
    body2 = resp2.json()
    assert body2["conversation_id"] == conv_id

    # The provider must have been called twice
    assert len(fake.call_history) == 2

    # The second call's messages must include the first user question in history
    second_call_messages = fake.call_history[1]
    message_contents = [msg["content"] for msg in second_call_messages if msg.get("content")]
    assert any(
        "What is the project structure?" in content for content in message_contents
    ), f"First turn not found in second call messages: {message_contents}"


def test_different_conversation_ids_are_isolated(
    client_with_fake_provider: tuple[TestClient, FakeLLMProvider],
) -> None:
    """Two separate conversation ids must not share memory."""

    client, fake = client_with_fake_provider

    resp_a = client.post("/api/chat", json={"message": "Hello from A", "conversation_id": "isolated-a"})
    resp_b = client.post("/api/chat", json={"message": "Hello from B", "conversation_id": "isolated-b"})

    assert resp_a.status_code == 200
    assert resp_b.status_code == 200

    # Follow-up for session A
    resp_a2 = client.post("/api/chat", json={"message": "Continue A", "conversation_id": "isolated-a"})
    assert resp_a2.status_code == 200

    # The third call is for session A; it must NOT contain "Hello from B"
    third_call_messages = fake.call_history[2]
    all_content = " ".join(str(msg.get("content", "")) for msg in third_call_messages)
    assert "Hello from B" not in all_content, "Session B content leaked into session A's memory"


def test_conversation_id_returned_when_not_provided(
    client_with_fake_provider: tuple[TestClient, FakeLLMProvider],
) -> None:
    """Server must generate and return a conversation_id when none is provided."""

    client, _ = client_with_fake_provider
    resp = client.post("/api/chat", json={"message": "Hello"})
    assert resp.status_code == 200
    body = resp.json()
    assert "conversation_id" in body
    assert len(body["conversation_id"]) > 0


def test_provided_conversation_id_echoed_back(
    client_with_fake_provider: tuple[TestClient, FakeLLMProvider],
) -> None:
    """Server must echo back the client-supplied conversation_id unchanged."""

    client, _ = client_with_fake_provider
    resp = client.post(
        "/api/chat",
        json={"message": "Hi", "conversation_id": "my-fixed-session-id"},
    )
    assert resp.status_code == 200
    assert resp.json()["conversation_id"] == "my-fixed-session-id"
