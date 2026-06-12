"""Tests for T-2 SQLite persistence: ConversationRepository and routes_session.

Covers:
- ensure_conversation creates and de-duplicates rows
- append_message records user/assistant turns
- recent_messages returns rows in chronological order, respects limit
- delete_conversation removes all rows
- GET /api/sessions/{id}/messages returns persisted messages
- DELETE /api/sessions/{id} removes conversation and drops in-memory session
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.db.repository import ConversationRepository

# ---------------------------------------------------------------------------
# Shared in-memory engine fixture
# ---------------------------------------------------------------------------


@pytest.fixture()
def memory_engine():
    """In-memory SQLite engine with tables created for each test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture()
def db_session(memory_engine):
    with Session(memory_engine) as session:
        yield session


@pytest.fixture()
def repo(db_session):
    return ConversationRepository(db_session)


# ---------------------------------------------------------------------------
# Unit tests: ConversationRepository
# ---------------------------------------------------------------------------


class TestEnsureConversation:
    def test_creates_new_conversation(self, repo: ConversationRepository) -> None:
        conv = repo.ensure_conversation("conv-1")
        assert conv.conversation_id == "conv-1"
        assert conv.id is not None

    def test_returns_existing_on_duplicate(self, repo: ConversationRepository) -> None:
        first = repo.ensure_conversation("conv-1")
        second = repo.ensure_conversation("conv-1")
        assert first.id == second.id

    def test_stores_title(self, repo: ConversationRepository) -> None:
        conv = repo.ensure_conversation("conv-2", title="My first question")
        assert conv.title == "My first question"


class TestAppendMessage:
    def test_appends_user_and_assistant_messages(self, repo: ConversationRepository) -> None:
        repo.ensure_conversation("conv-3")
        repo.append_message("conv-3", "user", "Hello")
        repo.append_message("conv-3", "assistant", "Hi there!")

        messages = repo.recent_messages("conv-3")
        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[0].content == "Hello"
        assert messages[1].role == "assistant"
        assert messages[1].content == "Hi there!"

    def test_appends_with_tool_calls_json(self, repo: ConversationRepository) -> None:
        repo.ensure_conversation("conv-4")
        repo.append_message("conv-4", "assistant", "", tool_calls_json='[{"name":"read_file"}]')
        messages = repo.recent_messages("conv-4")
        assert messages[0].tool_calls_json == '[{"name":"read_file"}]'


class TestRecentMessages:
    def test_returns_oldest_first(self, repo: ConversationRepository) -> None:
        repo.ensure_conversation("conv-5")
        for i in range(5):
            repo.append_message("conv-5", "user", f"msg {i}")
        messages = repo.recent_messages("conv-5")
        contents = [m.content for m in messages]
        assert contents == [f"msg {i}" for i in range(5)]

    def test_respects_limit(self, repo: ConversationRepository) -> None:
        repo.ensure_conversation("conv-6")
        for i in range(10):
            repo.append_message("conv-6", "user", f"msg {i}")
        messages = repo.recent_messages("conv-6", limit=3)
        assert len(messages) == 3
        # Should return the 3 most recent
        assert messages[-1].content == "msg 9"

    def test_returns_empty_for_unknown_conversation(self, repo: ConversationRepository) -> None:
        messages = repo.recent_messages("nonexistent")
        assert messages == []


class TestDeleteConversation:
    def test_deletes_conversation_and_messages(self, repo: ConversationRepository) -> None:
        repo.ensure_conversation("conv-7")
        repo.append_message("conv-7", "user", "Hello")
        repo.append_message("conv-7", "assistant", "World")

        repo.delete_conversation("conv-7")

        assert repo.recent_messages("conv-7") == []

    def test_delete_nonexistent_is_noop(self, repo: ConversationRepository) -> None:
        # Should not raise
        repo.delete_conversation("does-not-exist")


# ---------------------------------------------------------------------------
# Integration tests: HTTP routes
# ---------------------------------------------------------------------------


@pytest.fixture()
def test_app(memory_engine):
    """FastAPI test client with DB overridden to use in-memory engine."""
    from sqlmodel import Session

    from app.db.engine import get_session
    from app.main import create_app

    application = create_app()

    def override_get_session():
        with Session(memory_engine) as session:
            yield session

    application.dependency_overrides[get_session] = override_get_session
    return TestClient(application)


class TestSessionRoutes:
    def test_get_messages_returns_persisted_data(self, test_app: TestClient, memory_engine) -> None:
        """Messages written via ConversationRepository appear in GET response."""
        with Session(memory_engine) as session:
            repo = ConversationRepository(session)
            repo.ensure_conversation("route-test-1")
            repo.append_message("route-test-1", "user", "What is this project?")
            repo.append_message("route-test-1", "assistant", "It is AICodePilot.")

        response = test_app.get("/api/sessions/route-test-1/messages")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["role"] == "user"
        assert data[1]["role"] == "assistant"

    def test_get_messages_empty_for_unknown(self, test_app: TestClient) -> None:
        response = test_app.get("/api/sessions/unknown-conv/messages")
        assert response.status_code == 200
        assert response.json() == []

    def test_delete_session_removes_records(self, test_app: TestClient, memory_engine) -> None:
        with Session(memory_engine) as session:
            repo = ConversationRepository(session)
            repo.ensure_conversation("route-del-1")
            repo.append_message("route-del-1", "user", "Delete me")

        response = test_app.delete("/api/sessions/route-del-1")
        assert response.status_code == 204

        # Verify records are gone
        with Session(memory_engine) as session:
            repo = ConversationRepository(session)
            assert repo.recent_messages("route-del-1") == []
