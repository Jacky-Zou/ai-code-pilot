import json
from typing import Any, Literal

from pydantic import BaseModel, Field

AgentEventType = Literal["thinking", "tool_start", "tool_end", "answer_delta", "done", "error"]


class AgentEvent(BaseModel):
    """One server-sent event emitted during streaming agent execution.

    The event type maps directly to the SSE `event:` field, and `data` is
    serialized into the SSE `data:` field. Keeping a single typed model makes
    the stream contract explicit and testable without coupling to HTTP details.
    """

    type: AgentEventType
    data: dict[str, Any] = Field(default_factory=dict)

    def to_sse(self) -> str:
        """Render as an SSE frame. Two trailing newlines terminate the event."""

        payload = json.dumps(self.data, ensure_ascii=False, default=str)
        return f"event: {self.type}\ndata: {payload}\n\n"
