from pathlib import Path

from app.agent.executor import AgentExecutor
from app.agent.schemas import AgentRequest
from app.core.config import Settings
from app.llm.base import BaseLLMProvider


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
