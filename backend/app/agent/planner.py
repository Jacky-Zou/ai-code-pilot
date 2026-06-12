"""Text-protocol parser — fallback path only.

This module is used exclusively when a provider does not implement
chat_with_tools(). The primary Agent path (T-3) uses native tool_calls
and never touches this parser. If you are debugging unexpected tool-call
behavior, check executor._run_tool_calling_loop first; only arrive here
if the provider raised NotImplementedError on chat_with_tools.
"""

import json
import re
from typing import Any

from app.agent.schemas import AgentAction
from app.core.exceptions import AICodePilotError

_TOOL_ACTION_TYPES = {
    "list_files",
    "read_file",
    "project_tree",
    "find_files",
    "search_text",
    "retrieve_code",
    "analyze_log",
    "run_command",
}
_JSON_CODE_BLOCK_PATTERN = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL | re.IGNORECASE)
_THINKING_TAG_PATTERN = re.compile(r"<thinking>.*?</thinking>", re.DOTALL | re.IGNORECASE)
_LOOSE_FINAL_PATTERN = re.compile(
    r'\{\s*"type"\s*:\s*"final"\s*,\s*"answer"\s*:\s*"(?P<answer>.*)"\s*\}\s*`*\s*$',
    re.DOTALL,
)
_XML_TOOL_PATTERN = re.compile(
    r"<(?P<tool>list_files|read_file|project_tree|find_files|search_text|retrieve_code|analyze_log|run_command)>\s*"
    r"(?P<body>.*?)"
    r"</(?P=tool)>",
    re.DOTALL | re.IGNORECASE,
)
_XML_FIELD_PATTERN = re.compile(r"<(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)>(?P<value>.*?)</(?P=name)>", re.DOTALL)


def parse_agent_action(raw_content: str) -> AgentAction:
    """Parse one model response into the executor's internal action schema.

    Different providers do not always obey the prompt byte-for-byte. DeepSeek,
    for example, commonly wraps JSON in Markdown fences and may put the tool
    name in `type` instead of returning `type=action` plus `tool=<name>`. The
    executor still needs a single deterministic action, so the planner accepts
    those provider variants and normalizes them before Pydantic validation.
    """

    xml_action = _parse_xml_tool_action(raw_content)
    if xml_action is not None:
        return xml_action

    payload = _load_first_json_object(raw_content)
    if payload is None:
        loose_final_answer = _parse_loose_final_answer(raw_content)
        if loose_final_answer is not None:
            return AgentAction(type="final", answer=loose_final_answer)
        return AgentAction(type="final", answer=_strip_private_thinking(raw_content))

    normalized_payload = _normalize_provider_payload(payload)
    try:
        return AgentAction.model_validate(normalized_payload)
    except Exception as exc:
        raise AICodePilotError(f"Invalid agent action payload: {raw_content}") from exc


def _load_first_json_object(raw_content: str) -> dict[str, Any] | None:
    stripped = raw_content.strip()
    for candidate in _json_candidates(stripped):
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload
    return None


def _json_candidates(stripped_content: str) -> list[str]:
    candidates = [stripped_content]
    candidates.extend(match.group(1).strip() for match in _JSON_CODE_BLOCK_PATTERN.finditer(stripped_content))
    return candidates


def _normalize_provider_payload(payload: dict[str, Any]) -> dict[str, Any]:
    action_type = payload.get("type")
    if action_type in _TOOL_ACTION_TYPES:
        return {
            "type": "action",
            "tool": action_type,
            "arguments": payload.get("arguments") or {},
        }
    if action_type == "final" and isinstance(payload.get("answer"), str):
        return {**payload, "answer": _strip_private_thinking(payload["answer"])}
    return payload


def _strip_private_thinking(content: str) -> str:
    return _THINKING_TAG_PATTERN.sub("", content).strip()


def _parse_loose_final_answer(content: str) -> str | None:
    """Extract final answers from provider JSON-like text with unescaped newlines.

    Some models produce the requested JSON envelope but place raw Markdown with
    literal newlines inside the JSON string. That is not valid JSON, but treating
    it as a final user-facing answer leaks the protocol envelope into the UI.
    """

    match = _LOOSE_FINAL_PATTERN.search(content.strip())
    if not match:
        return None
    answer = match.group("answer")
    return _strip_private_thinking(answer).replace('\\"', '"').strip()


def _parse_xml_tool_action(content: str) -> AgentAction | None:
    match = _XML_TOOL_PATTERN.search(content)
    if not match:
        return None

    arguments: dict[str, Any] = {}
    for field_match in _XML_FIELD_PATTERN.finditer(match.group("body")):
        arguments[field_match.group("name")] = field_match.group("value").strip()

    return AgentAction(
        type="action",
        tool=match.group("tool").lower(),
        arguments=arguments,
    )
