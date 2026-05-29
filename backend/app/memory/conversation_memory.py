from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

MessageRole = Literal["user", "assistant", "tool", "system"]


@dataclass(frozen=True)
class MemoryMessage:
    """A single immutable message kept in bounded conversation memory."""

    role: MessageRole
    content: str
    conversation_id: str
    created_at: datetime
    metadata: dict[str, str]

    def to_llm_message(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


class ConversationMemory:
    """Bounded in-memory conversation history for Agent follow-up questions.

    The class intentionally stores only recent context. AICodePilot is a local
    developer assistant, so unbounded memory would make prompts grow silently,
    leak stale project context into later tasks, and increase model cost. The
    default limit is expressed in user/assistant turns rather than raw messages
    because users naturally reason about conversations as turns.
    """

    def __init__(self, max_turns: int = 8, conversation_id: str | None = None) -> None:
        if max_turns < 1:
            raise ValueError("max_turns must be at least 1")
        self.max_turns = max_turns
        self.conversation_id = conversation_id or str(uuid4())
        self._messages: deque[MemoryMessage] = deque()

    @property
    def messages(self) -> list[MemoryMessage]:
        """Return a snapshot so callers cannot mutate internal queue state."""

        return list(self._messages)

    def add_user_message(self, content: str, metadata: dict[str, str] | None = None) -> MemoryMessage:
        return self.add_message("user", content, metadata=metadata)

    def add_assistant_message(self, content: str, metadata: dict[str, str] | None = None) -> MemoryMessage:
        return self.add_message("assistant", content, metadata=metadata)

    def add_tool_message(self, content: str, metadata: dict[str, str] | None = None) -> MemoryMessage:
        return self.add_message("tool", content, metadata=metadata)

    def add_message(
        self,
        role: MessageRole,
        content: str,
        metadata: dict[str, str] | None = None,
    ) -> MemoryMessage:
        cleaned = content.strip()
        if not cleaned:
            raise ValueError("message content cannot be empty")

        message = MemoryMessage(
            role=role,
            content=cleaned,
            conversation_id=self.conversation_id,
            created_at=datetime.now(timezone.utc),
            metadata=dict(metadata or {}),
        )
        self._messages.append(message)
        self._trim_to_recent_turns()
        return message

    def to_llm_messages(self, system_message: str | None = None) -> list[dict[str, str]]:
        """Export memory in the role/content format expected by LLM providers.

        A supplied system message is prepended at export time instead of being
        stored in the rolling memory. This keeps policy/tool instructions stable
        while the user-facing conversation history remains bounded.
        """

        messages: list[dict[str, str]] = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.extend(message.to_llm_message() for message in self._messages)
        return messages

    def clear(self) -> None:
        self._messages.clear()

    def summary(self) -> dict[str, int | str]:
        return {
            "conversation_id": self.conversation_id,
            "max_turns": self.max_turns,
            "message_count": len(self._messages),
            "turn_count": self._count_user_turns(),
        }

    def _trim_to_recent_turns(self) -> None:
        """Keep only the latest N user turns and their following context.

        Tool results and assistant replies belong to the most recent user turn
        before them, so trimming starts at the earliest user message that should
        remain. Any prelude before that user message is discarded as stale.
        """

        user_indexes = [index for index, message in enumerate(self._messages) if message.role == "user"]
        if len(user_indexes) <= self.max_turns:
            return

        first_kept_index = user_indexes[-self.max_turns]
        for _ in range(first_kept_index):
            self._messages.popleft()

    def _count_user_turns(self) -> int:
        return sum(1 for message in self._messages if message.role == "user")
