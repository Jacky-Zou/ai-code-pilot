import pytest
from pydantic import ValidationError

from app.agent.schemas import AgentAction, AgentRequest, AgentResponse, ToolResult


def test_agent_request_requires_message() -> None:
    with pytest.raises(ValidationError):
        AgentRequest(message="")


def test_agent_action_schema_for_tool_call() -> None:
    action = AgentAction(type="action", tool="list_files", arguments={"project_path": "."})

    assert action.tool == "list_files"
    assert action.arguments["project_path"] == "."


def test_agent_response_defaults() -> None:
    response = AgentResponse(answer="ok", provider="openai", model="gpt-5.2")

    assert response.tool_calls == []
    assert response.references == []


def test_tool_result_can_store_error() -> None:
    result = ToolResult(name="read_file", error="missing")

    assert result.error == "missing"

