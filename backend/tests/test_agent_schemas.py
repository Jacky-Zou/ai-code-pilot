import pytest
from pydantic import ValidationError

from app.agent.schemas import AgentAction, AgentRequest, AgentResponse, PatchSuggestion, ToolResult


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
    assert response.patch_suggestions == []


def test_tool_result_can_store_error() -> None:
    result = ToolResult(name="read_file", error="missing")

    assert result.error == "missing"


def test_agent_response_can_store_patch_suggestions() -> None:
    patch = PatchSuggestion(file_path="app.py", diff="--- a/app.py\n+++ b/app.py\n@@\n-old\n+new")
    response = AgentResponse(answer="ok", provider="openai", model="gpt-5.2", patch_suggestions=[patch])

    assert response.patch_suggestions[0].file_path == "app.py"

