"""Tests for SSE streaming chat endpoint (T-6).

Verifies /api/chat/stream emits correct SSE event sequence:
  thinking → tool_start → tool_end → done
And that done event contains conversation_id and non-empty answer.
"""

import json
from typing import Any

from fastapi.testclient import TestClient

from app.llm.base import BaseLLMProvider
from app.llm.schemas import ChatResult, LLMToolCall
from app.main import create_app

# ---------------------------------------------------------------------------
# Fake provider that returns one tool call then a final answer
# ---------------------------------------------------------------------------


class StreamFakeProvider(BaseLLMProvider):
    """Returns a single read_file tool call, then a final answer."""

    provider_name = "openai"

    def __init__(self) -> None:
        self._calls = 0

    def chat(self, messages: list[dict[str, Any]], model: str | None = None, **kwargs: Any) -> str:
        return '{"type":"final","answer":"stream fallback answer"}'

    def chat_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        model: str | None = None,
    ) -> ChatResult:
        self._calls += 1
        if self._calls == 1:
            return ChatResult(
                content=None,
                tool_calls=[LLMToolCall(id="c1", name="list_files", arguments={})],
            )
        return ChatResult(content="Stream answer: found project files.", tool_calls=[])


class NoToolCallFakeProvider(BaseLLMProvider):
    """Returns a final answer immediately without any tool calls."""

    provider_name = "openai"

    def chat(self, messages, model=None, **kwargs):
        return '{"type":"final","answer":"direct answer"}'

    def chat_with_tools(self, messages, tools, model=None) -> ChatResult:
        return ChatResult(content="Direct stream answer.", tool_calls=[])


# ---------------------------------------------------------------------------
# SSE frame parser
# ---------------------------------------------------------------------------


def parse_sse_frames(raw: str) -> list[dict[str, Any]]:
    """Parse a raw SSE response body into a list of {type, data} dicts."""

    events = []
    for frame in raw.split("\n\n"):
        frame = frame.strip()
        if not frame:
            continue
        event_type = "message"
        data_lines: list[str] = []
        for line in frame.split("\n"):
            if line.startswith("event:"):
                event_type = line[6:].strip()
            elif line.startswith("data:"):
                data_lines.append(line[5:].strip())
        if data_lines:
            try:
                data = json.loads("\n".join(data_lines))
            except json.JSONDecodeError:
                data = {}
            events.append({"type": event_type, "data": data})
    return events


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestChatStreamEndpoint:
    def _make_client(self, provider: BaseLLMProvider) -> TestClient:
        from app.agent.executor import AgentExecutor
        from app.api.routes_chat import get_agent

        app = create_app()

        def fake_agent() -> "BaseLLMProvider":
            from app.agent.agent import AICodePilotAgent

            return AICodePilotAgent(executor=AgentExecutor(llm_provider=provider))

        app.dependency_overrides[get_agent] = fake_agent
        return TestClient(app, raise_server_exceptions=True)

    def test_stream_emits_thinking_tool_start_tool_end_done(self, tmp_path) -> None:
        """Full happy-path: thinking → tool_start → tool_end → done."""

        (tmp_path / "readme.md").write_text("# Project\n", encoding="utf-8")
        client = self._make_client(StreamFakeProvider())

        response = client.post(
            "/api/chat/stream",
            json={"message": "list files", "project_path": str(tmp_path)},
        )
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

        events = parse_sse_frames(response.text)
        event_types = [e["type"] for e in events]

        assert "thinking" in event_types, f"No thinking event: {event_types}"
        assert "tool_start" in event_types, f"No tool_start event: {event_types}"
        assert "tool_end" in event_types, f"No tool_end event: {event_types}"
        assert "done" in event_types, f"No done event: {event_types}"

    def test_stream_done_event_has_answer(self, tmp_path) -> None:
        (tmp_path / "f.py").write_text("# f\n", encoding="utf-8")
        client = self._make_client(StreamFakeProvider())

        response = client.post(
            "/api/chat/stream",
            json={"message": "list files", "project_path": str(tmp_path)},
        )
        events = parse_sse_frames(response.text)
        done_events = [e for e in events if e["type"] == "done"]

        assert len(done_events) == 1
        assert done_events[0]["data"]["answer"]  # non-empty answer

    def test_stream_done_event_has_conversation_id(self, tmp_path) -> None:
        client = self._make_client(NoToolCallFakeProvider())

        response = client.post(
            "/api/chat/stream",
            json={"message": "hello"},
        )
        events = parse_sse_frames(response.text)
        done_events = [e for e in events if e["type"] == "done"]

        assert len(done_events) == 1
        assert "conversation_id" in done_events[0]["data"]
        assert done_events[0]["data"]["conversation_id"]

    def test_stream_client_supplied_conversation_id_echoed(self) -> None:
        client = self._make_client(NoToolCallFakeProvider())

        response = client.post(
            "/api/chat/stream",
            json={"message": "hello", "conversation_id": "my-stream-session"},
        )
        events = parse_sse_frames(response.text)
        done = next(e for e in events if e["type"] == "done")
        assert done["data"]["conversation_id"] == "my-stream-session"

    def test_stream_tool_start_contains_tool_name(self, tmp_path) -> None:
        (tmp_path / "f.py").write_text("# f\n", encoding="utf-8")
        client = self._make_client(StreamFakeProvider())

        response = client.post(
            "/api/chat/stream",
            json={"message": "list files", "project_path": str(tmp_path)},
        )
        events = parse_sse_frames(response.text)
        tool_starts = [e for e in events if e["type"] == "tool_start"]

        assert tool_starts
        assert tool_starts[0]["data"]["tool"] == "list_files"

    def test_stream_done_event_contains_tool_calls_list(self, tmp_path) -> None:
        (tmp_path / "f.py").write_text("# f\n", encoding="utf-8")
        client = self._make_client(StreamFakeProvider())

        response = client.post(
            "/api/chat/stream",
            json={"message": "list files", "project_path": str(tmp_path)},
        )
        events = parse_sse_frames(response.text)
        done = next(e for e in events if e["type"] == "done")
        assert "tool_calls" in done["data"]
        assert isinstance(done["data"]["tool_calls"], list)
        assert len(done["data"]["tool_calls"]) >= 1

    def test_stream_no_tool_calls_still_emits_done(self) -> None:
        """Provider returning final answer immediately should still emit done."""

        client = self._make_client(NoToolCallFakeProvider())
        response = client.post("/api/chat/stream", json={"message": "hello"})
        events = parse_sse_frames(response.text)
        assert any(e["type"] == "done" for e in events)

    def test_stream_ordered_events(self, tmp_path) -> None:
        """thinking must precede tool_start; tool_end must follow tool_start."""

        (tmp_path / "f.py").write_text("# f\n", encoding="utf-8")
        client = self._make_client(StreamFakeProvider())

        response = client.post(
            "/api/chat/stream",
            json={"message": "list files", "project_path": str(tmp_path)},
        )
        event_types = [e["type"] for e in parse_sse_frames(response.text)]

        if "tool_start" in event_types:
            thinking_idx = event_types.index("thinking")
            tool_start_idx = event_types.index("tool_start")
            tool_end_idx = event_types.index("tool_end")
            assert thinking_idx < tool_start_idx < tool_end_idx
