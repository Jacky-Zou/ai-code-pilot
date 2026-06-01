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


def test_executor_executes_provider_tool_type_markdown_action(tmp_path: Path) -> None:
    agent_file = tmp_path / "agent" / "agent.py"
    agent_file.parent.mkdir()
    agent_file.write_text("class AICodePilotAgent:\n    pass\n", encoding="utf-8")
    provider = FakeProvider(
        [
            """```json
{"type":"read_file","arguments":{"file_path":"agent/agent.py","max_bytes":50000}}
```
```json
{"type":"read_file","arguments":{"file_path":"agent/__init__.py","max_bytes":50000}}
```""",
            '{"type":"final","answer":"Agent main flow is implemented in agent/agent.py."}',
        ]
    )
    executor = AgentExecutor(llm_provider=provider, settings=Settings(_env_file=None))

    response = executor.run(AgentRequest(message="where is agent flow", project_path=str(tmp_path)))

    assert response.answer == "Agent main flow is implemented in agent/agent.py."
    assert response.tool_calls[0].name == "read_file"
    assert response.tool_calls[0].error is None
    assert response.references[0].file_path == "agent/agent.py"
    assert len(provider.calls) == 2


def test_executor_continues_until_final_after_multiple_tool_actions(tmp_path: Path) -> None:
    (tmp_path / "main.py").write_text("from agent.agent import AICodePilotAgent\n", encoding="utf-8")
    agent_file = tmp_path / "agent" / "agent.py"
    agent_file.parent.mkdir()
    agent_file.write_text("class AICodePilotAgent:\n    def run(self):\n        pass\n", encoding="utf-8")
    provider = FakeProvider(
        [
            '{"type":"read_file","arguments":{"file_path":"main.py"}}',
            '{"type":"read_file","arguments":{"file_path":"agent/agent.py"}}',
            '{"type":"final","answer":"Agent flow starts in main.py and is implemented in agent/agent.py."}',
        ]
    )
    executor = AgentExecutor(llm_provider=provider, settings=Settings(_env_file=None))

    response = executor.run(AgentRequest(message="where is agent flow", project_path=str(tmp_path)))

    assert response.answer == "Agent flow starts in main.py and is implemented in agent/agent.py."
    assert [tool_call.name for tool_call in response.tool_calls] == ["read_file", "read_file"]
    assert [reference.file_path for reference in response.references] == ["main.py", "agent/agent.py"]
    assert len(provider.calls) == 3


def test_executor_reprompts_when_final_answer_only_contains_thinking(tmp_path: Path) -> None:
    (tmp_path / "main.py").write_text("from agent.agent import AICodePilotAgent\n", encoding="utf-8")
    provider = FakeProvider(
        [
            '{"type":"read_file","arguments":{"file_path":"main.py"}}',
            "<thinking>I need to answer now</thinking>",
            '{"type":"final","answer":"Agent startup imports AICodePilotAgent from main.py."}',
        ]
    )
    executor = AgentExecutor(llm_provider=provider, settings=Settings(_env_file=None))

    response = executor.run(AgentRequest(message="where is agent flow", project_path=str(tmp_path)))

    assert response.answer == "Agent startup imports AICodePilotAgent from main.py."
    assert response.tool_calls[0].name == "read_file"
    assert len(provider.calls) == 3


def test_executor_replaces_protocol_leak_with_tool_result_summary(tmp_path: Path) -> None:
    (tmp_path / "agent.py").write_text("class AgentExecutor:\n    pass\n", encoding="utf-8")
    provider = FakeProvider(
        [
            '{"type":"read_file","arguments":{"file_path":"agent.py"}}',
            """```json
{"type":"read_file","arguments":{"file_path":"agent.py","max_bytes":50000}}
```""",
            """```json
{"type":"read_file","arguments":{"file_path":"agent.py","max_bytes":50000}}
```""",
            """```json
{"type":"read_file","arguments":{"file_path":"agent.py","max_bytes":50000}}
```""",
            """```json
{"type":"read_file","arguments":{"file_path":"agent.py","max_bytes":50000}}
```""",
        ]
    )
    executor = AgentExecutor(llm_provider=provider, settings=Settings(_env_file=None))

    response = executor.run(AgentRequest(message="where is the agent flow", project_path=str(tmp_path)))

    assert "```json" not in response.answer
    assert '"type":"read_file"' not in response.answer
    assert "Read `agent.py`" in response.answer
    assert response.tool_calls[0].name == "read_file"


def test_executor_uses_chinese_fallback_for_chinese_requests(tmp_path: Path) -> None:
    agent_file = tmp_path / "backend" / "app" / "agent" / "agent.py"
    agent_file.parent.mkdir(parents=True)
    agent_file.write_text("class AICodePilotAgent:\n    pass\n", encoding="utf-8")
    provider = FakeProvider(
        [
            '{"type":"read_file","arguments":{"file_path":"backend/app/agent/agent.py"}}',
            '{"type":"read_file","arguments":{"file_path":"backend/app/agent/agent.py"}}',
            '{"type":"read_file","arguments":{"file_path":"backend/app/agent/agent.py"}}',
            '{"type":"read_file","arguments":{"file_path":"backend/app/agent/agent.py"}}',
            '{"type":"read_file","arguments":{"file_path":"backend/app/agent/agent.py"}}',
        ]
    )
    executor = AgentExecutor(llm_provider=provider, settings=Settings(_env_file=None))

    response = executor.run(AgentRequest(message="请分析 Agent 主流程在哪里", project_path=str(tmp_path)))

    assert "Agent 门面入口" in response.answer
    assert "```json" not in response.answer
    assert '"type"' not in response.answer


def test_executor_replaces_english_answer_for_chinese_request(tmp_path: Path) -> None:
    (tmp_path / "backend" / "app" / "agent").mkdir(parents=True)
    (tmp_path / "backend" / "app" / "agent" / "executor.py").write_text(
        "class AgentExecutor:\n    pass\n",
        encoding="utf-8",
    )
    provider = FakeProvider(
        [
            '{"type":"read_file","arguments":{"file_path":"backend/app/agent/executor.py"}}',
            '{"type":"final","answer":"The agent flow is implemented in executor.py."}',
        ]
    )
    executor = AgentExecutor(llm_provider=provider, settings=Settings(_env_file=None))

    response = executor.run(AgentRequest(message="请分析 Agent 主流程在哪里", project_path=str(tmp_path)))

    assert "核心执行闭环" in response.answer
    assert "The agent flow" not in response.answer


def test_executor_requests_final_summary_after_tool_budget(tmp_path: Path) -> None:
    for index in range(1, 6):
        (tmp_path / f"file_{index}.py").write_text(f"# file {index}\n", encoding="utf-8")

    provider = FakeProvider(
        [f'{{"type":"read_file","arguments":{{"file_path":"file_{index}.py"}}}}' for index in range(1, 6)]
        + ['{"type":"final","answer":"Agent flow summary after collecting enough context."}']
    )
    executor = AgentExecutor(llm_provider=provider, settings=Settings(_env_file=None))

    response = executor.run(AgentRequest(message="summarize agent flow", project_path=str(tmp_path)))

    assert response.answer == "Agent flow summary after collecting enough context."
    assert len(response.tool_calls) == 5
    assert len(provider.calls) == 6
    assert [message["role"] for message in provider.calls[-1]] == ["system", "user"]
    assert '"type":"read_file"' not in provider.calls[-1][-1]["content"]


def test_executor_executes_xml_tool_call_payload(tmp_path: Path) -> None:
    (tmp_path / "main.py").write_text("from agent.agent import AICodePilotAgent\n", encoding="utf-8")
    provider = FakeProvider(
        [
            """<tool_calls>
<read_file>
<file_path>main.py</file_path>
</read_file>
</tool_calls>""",
            '{"type":"final","answer":"Agent startup is visible in main.py."}',
        ]
    )
    executor = AgentExecutor(llm_provider=provider, settings=Settings(_env_file=None))

    response = executor.run(AgentRequest(message="where is agent flow", project_path=str(tmp_path)))

    assert response.answer == "Agent startup is visible in main.py."
    assert response.tool_calls[0].name == "read_file"
    assert response.references[0].file_path == "main.py"
