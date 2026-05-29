import pytest

from app.agent.planner import parse_agent_action
from app.core.exceptions import AICodePilotError


def test_parse_agent_action_treats_plain_text_as_final_answer() -> None:
    action = parse_agent_action("Plain answer from the model")

    assert action.type == "final"
    assert action.answer == "Plain answer from the model"


def test_parse_agent_action_accepts_structured_tool_action() -> None:
    action = parse_agent_action('{"type":"action","tool":"read_file","arguments":{"file_path":"README.md"}}')

    assert action.type == "action"
    assert action.tool == "read_file"
    assert action.arguments == {"file_path": "README.md"}


def test_parse_agent_action_rejects_invalid_structured_payload() -> None:
    with pytest.raises(AICodePilotError, match="Invalid agent action payload"):
        parse_agent_action('{"type":"unknown","answer":"nope"}')
