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


def test_parse_agent_action_accepts_markdown_json_code_block() -> None:
    raw = """```json
{"type":"action","tool":"retrieve_code","arguments":{"query":"agent flow"}}
```"""

    action = parse_agent_action(raw)

    assert action.type == "action"
    assert action.tool == "retrieve_code"
    assert action.arguments == {"query": "agent flow"}


def test_parse_agent_action_normalizes_provider_tool_type_payload() -> None:
    raw = """```json
{"type":"read_file","arguments":{"file_path":"/app/app/agent/agent.py","max_bytes":50000}}
```"""

    action = parse_agent_action(raw)

    assert action.type == "action"
    assert action.tool == "read_file"
    assert action.arguments == {"file_path": "/app/app/agent/agent.py", "max_bytes": 50000}


def test_parse_agent_action_uses_first_json_block_when_model_lists_multiple_actions() -> None:
    raw = """```json
{"type":"read_file","arguments":{"file_path":"/app/app/main.py"}}
```
```json
{"type":"read_file","arguments":{"file_path":"/app/app/agent/agent.py"}}
```"""

    action = parse_agent_action(raw)

    assert action.type == "action"
    assert action.tool == "read_file"
    assert action.arguments == {"file_path": "/app/app/main.py"}


def test_parse_agent_action_strips_private_thinking_tags_from_plain_final() -> None:
    action = parse_agent_action("<thinking>internal notes</thinking>Final answer")

    assert action.type == "final"
    assert action.answer == "Final answer"


def test_parse_agent_action_strips_private_thinking_tags_from_json_final() -> None:
    action = parse_agent_action('{"type":"final","answer":"<thinking>hidden</thinking>Visible answer"}')

    assert action.type == "final"
    assert action.answer == "Visible answer"


def test_parse_agent_action_unwraps_loose_multiline_final_json() -> None:
    raw = '{"type":"final","answer":"Line one\n\n## Heading\nLine two"}'

    action = parse_agent_action(raw)

    assert action.type == "final"
    assert action.answer == "Line one\n\n## Heading\nLine two"


def test_parse_agent_action_accepts_xml_tool_call_payload() -> None:
    raw = """<tool_calls>
<read_file>
<file_path>agent/executor.py</file_path>
<project_path>/app/app</project_path>
</read_file>
</tool_calls>"""

    action = parse_agent_action(raw)

    assert action.type == "action"
    assert action.tool == "read_file"
    assert action.arguments == {"file_path": "agent/executor.py", "project_path": "/app/app"}


def test_parse_agent_action_unwraps_loose_final_json_with_trailing_fence() -> None:
    raw = '{"type":"final","answer":"Useful answer with `code`"}\n```'

    action = parse_agent_action(raw)

    assert action.type == "final"
    assert action.answer == "Useful answer with `code`"
