from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import BaseModel, Field

MessageRole = Literal["system", "user", "assistant", "tool"]


class Message(BaseModel):
    role: MessageRole
    content: str

    def to_api_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


class LLMResponse(BaseModel):
    content: str
    provider: str
    model: str
    raw: dict[str, Any] | None = Field(default=None)


@dataclass
class LLMToolCall:
    """One tool invocation returned by the model in tool-calling mode.

    `id` is required by OpenAI's protocol and must be echoed back in the
    tool-result message so the model can correlate results to calls. When a
    provider does not supply an id (e.g. test doubles), a generated value is
    acceptable.
    """

    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class ChatResult:
    """Unified result from a chat completion call.

    When the model returns tool calls, content is typically None (OpenAI
    convention). When it returns a final text answer, tool_calls is empty.
    Both provider paths must produce this shape so the executor can consume
    them uniformly regardless of which mode was used.
    """

    content: str | None
    tool_calls: list[LLMToolCall] = field(default_factory=list)

    @property
    def has_tool_calls(self) -> bool:
        return bool(self.tool_calls)

    @property
    def is_final(self) -> bool:
        return not self.has_tool_calls and self.content is not None
