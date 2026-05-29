from pathlib import Path
from typing import Any

from pydantic import BaseModel

from app.agent.executor import AgentExecutor
from app.agent.schemas import AgentRequest
from app.core.config import Settings
from app.llm.base import BaseLLMProvider
from app.memory.conversation_memory import ConversationMemory
from app.tools.base import BaseTool
from app.tools.registry import ToolRegistry


class FakeProvider(BaseLLMProvider):
    provider_name = "fake"

    def __init__(self, responses: list[str]) -> None:
        self.responses = responses
        self.calls: list[list[dict[str, str]]] = []

    def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        **kwargs: object,
    ) -> str:
        self.calls.append(messages)
        return self.responses.pop(0)


def test_executor_returns_final_answer_without_tool() -> None:
    provider = FakeProvider(['{"type":"final","answer":"done"}'])
    executor = AgentExecutor(llm_provider=provider, settings=Settings(_env_file=None))

    response = executor.run(AgentRequest(message="hello"))

    assert response.answer == "done"
    assert response.tool_calls == []


def test_executor_calls_tool_and_summarizes(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("FastAPI example", encoding="utf-8")
    provider = FakeProvider(
        [
            '{"type":"action","tool":"search_text","arguments":{"keyword":"FastAPI"}}',
            '{"type":"final","answer":"Found FastAPI in README.md"}',
        ]
    )
    executor = AgentExecutor(llm_provider=provider, settings=Settings(_env_file=None))

    response = executor.run(AgentRequest(message="search FastAPI", project_path=str(tmp_path)))

    assert response.answer == "Found FastAPI in README.md"
    assert response.tool_calls[0].name == "search_text"
    assert response.tool_calls[0].error is None
    assert response.references[0].file_path == "README.md"
    assert response.references[0].line_number == 1
    assert len(provider.calls) == 2


def test_executor_calls_retrieve_code_tool(tmp_path: Path) -> None:
    (tmp_path / "agent.py").write_text("class AgentExecutor:\n    pass", encoding="utf-8")
    provider = FakeProvider(
        [
            '{"type":"action","tool":"retrieve_code","arguments":{"query":"AgentExecutor"}}',
            '{"type":"final","answer":"Agent flow is in agent.py"}',
        ]
    )
    executor = AgentExecutor(llm_provider=provider, settings=Settings(_env_file=None))

    response = executor.run(AgentRequest(message="where is agent flow", project_path=str(tmp_path)))

    assert response.answer == "Agent flow is in agent.py"
    assert response.tool_calls[0].name == "retrieve_code"
    assert response.references[0].file_path == "agent.py"
    assert response.references[0].line_number == 1


class CaptureArgs(BaseModel):
    project_path: str


class CaptureProjectPathTool(BaseTool):
    name = "run_command"
    description = "Capture project path injection"
    args_schema = CaptureArgs

    def run(self, **kwargs: Any) -> dict[str, Any]:
        return {
            "patch_suggestions": [
                {
                    "file_path": "app.py",
                    "diff": "--- a/app.py\n+++ b/app.py\n@@\n-old\n+new",
                    "summary": "Demo patch",
                }
            ],
            "project_path": kwargs["project_path"],
        }


def test_executor_connects_memory_project_path_and_patch_suggestions(tmp_path: Path) -> None:
    registry = ToolRegistry()
    registry.register(CaptureProjectPathTool())
    memory = ConversationMemory(conversation_id="session", max_turns=3)
    memory.add_user_message("previous question")
    memory.add_assistant_message("previous answer")
    provider = FakeProvider(
        [
            '{"type":"action","tool":"run_command","arguments":{}}',
            '{"type":"final","answer":"Patch suggestion prepared"}',
        ]
    )
    executor = AgentExecutor(
        registry=registry,
        llm_provider=provider,
        memory=memory,
        settings=Settings(_env_file=None),
    )

    response = executor.run(AgentRequest(message="prepare patch", project_path=str(tmp_path)))

    assert response.tool_calls[0].arguments["project_path"] == str(tmp_path)
    assert response.patch_suggestions[0].file_path == "app.py"
    assert response.patch_suggestions[0].summary == "Demo patch"
    assert provider.calls[0][1]["content"] == "previous question"
    assert provider.calls[0][-1]["content"].endswith("User request: prepare patch")
    assert memory.summary()["turn_count"] == 2
