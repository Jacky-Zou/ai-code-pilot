import json

from app.agent.schemas import AgentAction
from app.core.exceptions import AICodePilotError


def parse_agent_action(raw_content: str) -> AgentAction:
    try:
        payload = json.loads(raw_content)
    except json.JSONDecodeError:
        return AgentAction(type="final", answer=raw_content)

    try:
        return AgentAction.model_validate(payload)
    except Exception as exc:
        raise AICodePilotError(f"Invalid agent action payload: {raw_content}") from exc
