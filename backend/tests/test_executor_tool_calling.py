"""Tests for native tool calling: OpenAI provider chat_with_tools + executor loop.

Covers T-3 requirements:
- chat_with_tools returns ChatResult with tool_calls
- executor _run_tool_calling_loop handles multi-step tool calls
- loop detection terminates identical back-to-back calls
- NotImplementedError triggers text-protocol fallback
- T-4: AGENT_MAX_STEPS config is respected
"""

import json
from typing import Any

import pytest

from app.agent.executor import AgentExecutor
from app.agent.schemas import AgentRequest
from app.core.config import Settings
from app.llm.base import BaseLLMProvider
from app.llm.client import extract_chat_result
from app.llm.schemas import ChatResult, LLMToolCall

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_tool_call_result(tool_name: str, args: dict[str, Any], call_id: str = "call_1") -> dict[str, Any]:
    """Build a minimal OpenAI-format chat completion response with a tool call."""

    return {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": call_id,
                            "type": "function",
                            "function": {
                                "name": tool_name,
                                "arguments": json.dumps(args),
                            },
                        }
                    ],
                }
            }
        ]
    }


def _make_final_result(content: str) -> dict[str, Any]:
    """Build a minimal OpenAI-format chat completion response with final text."""

    return {"choices": [{"message": {"role": "assistant", "content": content, "tool_calls": []}}]}


# ---------------------------------------------------------------------------
# extract_chat_result unit tests
# ---------------------------------------------------------------------------


class TestExtractChatResult:
    def test_extracts_tool_calls(self) -> None:
        data = _make_tool_call_result("read_file", {"file_path": "main.py"})
        result = extract_chat_result(data)
        assert result.has_tool_calls
        assert result.tool_calls[0].name == "read_file"
        assert result.tool_calls[0].arguments == {"file_path": "main.py"}
        assert result.tool_calls[0].id == "call_1"

    def test_extracts_final_content(self) -> None:
        data = _make_final_result("Here is the answer.")
        result = extract_chat_result(data)
        assert result.is_final
        assert result.content == "Here is the answer."
        assert not result.has_tool_calls

    def test_raises_on_neither_content_nor_tool_calls(self) -> None:
        from app.core.exceptions import LLMProviderError

        data = {"choices": [{"message": {"role": "assistant", "content": None, "tool_calls": []}}]}
        with pytest.raises(LLMProviderError, match="neither content nor tool_calls"):
            extract_chat_result(data)

    def test_raises_on_malformed_tool_call(self) -> None:
        from app.core.exceptions import LLMProviderError

        data = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [{"id": "x", "function": {"name": "t", "arguments": "NOT JSON"}}],
                    }
                }
            ]
        }
        with pytest.raises(LLMProviderError, match="Malformed tool_call"):
            extract_chat_result(data)

    def test_raises_on_missing_choices(self) -> None:
        from app.core.exceptions import LLMProviderError

        with pytest.raises(LLMProviderError):
            extract_chat_result({})


# ---------------------------------------------------------------------------
# FakeProvider for tool-calling tests: returns ChatResult objects
# ---------------------------------------------------------------------------


class NativeToolCallFakeProvider(BaseLLMProvider):
    """Fake provider that returns ChatResult from chat_with_tools."""

    provider_name = "openai"

    def __init__(self, results: list[ChatResult]) -> None:
        self._results = list(results)
        self.calls: list[list[dict[str, Any]]] = []

    def chat(self, messages: list[dict[str, Any]], model: str | None = None, **kwargs: Any) -> str:
        self.calls.append(list(messages))
        # Finalizer synthesis: return a simple final JSON
        return '{"type":"final","answer":"fallback final answer"}'

    def chat_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        model: str | None = None,
    ) -> ChatResult:
        self.calls.append(list(messages))
        return self._results.pop(0)


# ---------------------------------------------------------------------------
# Executor tool-calling loop tests
# ---------------------------------------------------------------------------


class TestExecutorToolCallingLoop:
    def test_single_tool_call_then_final(self, tmp_path) -> None:
        """One tool call followed by a final answer completes successfully."""

        (tmp_path / "main.py").write_text("from agent import Agent\n", encoding="utf-8")
        tc = LLMToolCall(id="c1", name="read_file", arguments={"file_path": "main.py"})
        provider = NativeToolCallFakeProvider(
            [
                ChatResult(content=None, tool_calls=[tc]),
                ChatResult(content="Agent is imported in main.py.", tool_calls=[]),
            ]
        )
        executor = AgentExecutor(llm_provider=provider, settings=Settings(_env_file=None))

        response = executor.run(AgentRequest(message="where is Agent?", project_path=str(tmp_path)))

        assert response.answer == "Agent is imported in main.py."
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0].name == "read_file"
        assert response.tool_calls[0].error is None
        assert len(provider.calls) == 2

    def test_multi_tool_calls_then_final(self, tmp_path) -> None:
        """Two sequential tool calls then a final answer."""

        (tmp_path / "a.py").write_text("# a\n", encoding="utf-8")
        (tmp_path / "b.py").write_text("# b\n", encoding="utf-8")
        tc1 = LLMToolCall(id="c1", name="read_file", arguments={"file_path": "a.py"})
        tc2 = LLMToolCall(id="c2", name="read_file", arguments={"file_path": "b.py"})
        provider = NativeToolCallFakeProvider(
            [
                ChatResult(content=None, tool_calls=[tc1]),
                ChatResult(content=None, tool_calls=[tc2]),
                ChatResult(content="Both files read.", tool_calls=[]),
            ]
        )
        executor = AgentExecutor(llm_provider=provider, settings=Settings(_env_file=None))

        response = executor.run(AgentRequest(message="read a and b", project_path=str(tmp_path)))

        assert response.answer == "Both files read."
        assert len(response.tool_calls) == 2
        assert [tc.name for tc in response.tool_calls] == ["read_file", "read_file"]

    def test_loop_detection_terminates_identical_calls(self, tmp_path) -> None:
        """Identical back-to-back tool calls are detected and the agent is steered to finish."""

        (tmp_path / "x.py").write_text("# x\n", encoding="utf-8")
        tc = LLMToolCall(id="c1", name="read_file", arguments={"file_path": "x.py"})
        # Model repeatedly returns the same tool call (loop). After detection the
        # executor injects an error result, so eventually the model produces final.
        provider = NativeToolCallFakeProvider(
            [
                ChatResult(content=None, tool_calls=[tc]),
                ChatResult(content=None, tool_calls=[tc]),  # identical → loop detected
                ChatResult(content="Stopped looping.", tool_calls=[]),
            ]
        )
        executor = AgentExecutor(llm_provider=provider, settings=Settings(_env_file=None))

        response = executor.run(AgentRequest(message="read x.py", project_path=str(tmp_path)))

        assert response.answer == "Stopped looping."
        # First call executed; second is the loop detection (injected error, not re-executed)
        assert len(response.tool_calls) == 1

    def test_not_implemented_falls_back_to_text_protocol(self, tmp_path) -> None:
        """Provider raising NotImplementedError causes executor to fall back."""

        (tmp_path / "main.py").write_text("# main\n", encoding="utf-8")

        class TextOnlyProvider(BaseLLMProvider):
            provider_name = "openai"

            def chat(self, messages, model=None, **kwargs):
                return '{"type":"final","answer":"text fallback answer"}'

            def chat_with_tools(self, messages, tools, model=None):
                raise NotImplementedError

        executor = AgentExecutor(llm_provider=TextOnlyProvider(), settings=Settings(_env_file=None))
        response = executor.run(AgentRequest(message="hello", project_path=str(tmp_path)))

        assert response.answer == "text fallback answer"

    def test_agent_max_steps_respected(self, tmp_path) -> None:
        """Executor must not exceed AGENT_MAX_STEPS tool calls."""

        (tmp_path / "f.py").write_text("# f\n", encoding="utf-8")
        tc = LLMToolCall(id="c1", name="read_file", arguments={"file_path": "f.py"})
        # Provide more results than max_steps allows + final
        provider = NativeToolCallFakeProvider(
            [
                ChatResult(content=None, tool_calls=[tc]),
                ChatResult(content=None, tool_calls=[tc]),
                ChatResult(content=None, tool_calls=[tc]),
                ChatResult(content=None, tool_calls=[tc]),
                ChatResult(content="Done within limit.", tool_calls=[]),
            ]
        )
        executor = AgentExecutor(llm_provider=provider, settings=Settings(AGENT_MAX_STEPS=3, _env_file=None))

        executor.run(AgentRequest(message="read f.py", project_path=str(tmp_path)))

        # With max_steps=3 and loop detection on identical calls, executor should
        # stop at 3 steps and request final summary.
        assert len(provider.calls) <= 4  # at most max_steps + 1 final summary call

    def test_project_path_injected_into_tool_args(self, tmp_path) -> None:
        """project_path is automatically injected for tools that need it."""

        (tmp_path / "readme.md").write_text("# README\n", encoding="utf-8")
        # Tool call without project_path in arguments
        tc = LLMToolCall(id="c1", name="read_file", arguments={"file_path": "readme.md"})
        provider = NativeToolCallFakeProvider(
            [
                ChatResult(content=None, tool_calls=[tc]),
                ChatResult(content="README is found.", tool_calls=[]),
            ]
        )
        executor = AgentExecutor(llm_provider=provider, settings=Settings(_env_file=None))

        response = executor.run(AgentRequest(message="read readme", project_path=str(tmp_path)))

        assert response.tool_calls[0].arguments.get("project_path") == str(tmp_path)
        assert response.answer == "README is found."

    def test_tool_error_does_not_crash_executor(self, tmp_path) -> None:
        """A tool that fails fills the error field but the loop continues."""

        tc = LLMToolCall(id="c1", name="read_file", arguments={"file_path": "nonexistent.py"})
        provider = NativeToolCallFakeProvider(
            [
                ChatResult(content=None, tool_calls=[tc]),
                ChatResult(content="File was not found.", tool_calls=[]),
            ]
        )
        executor = AgentExecutor(llm_provider=provider, settings=Settings(_env_file=None))

        response = executor.run(AgentRequest(message="read it", project_path=str(tmp_path)))

        assert response.tool_calls[0].error is not None
        assert response.answer == "File was not found."


# ---------------------------------------------------------------------------
# T-4: AGENT_MAX_STEPS configuration
# ---------------------------------------------------------------------------


class TestAgentMaxStepsConfig:
    def test_default_max_steps_is_10(self) -> None:
        settings = Settings(_env_file=None)
        assert settings.agent_max_steps == 10

    def test_custom_max_steps_via_env(self) -> None:
        settings = Settings(AGENT_MAX_STEPS=7, _env_file=None)
        assert settings.agent_max_steps == 7

    def test_max_steps_lower_bound(self) -> None:
        with pytest.raises(Exception):
            Settings(AGENT_MAX_STEPS=2, _env_file=None)

    def test_max_steps_upper_bound(self) -> None:
        with pytest.raises(Exception):
            Settings(AGENT_MAX_STEPS=31, _env_file=None)
