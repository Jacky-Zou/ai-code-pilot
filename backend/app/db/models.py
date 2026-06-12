from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Conversation(SQLModel, table=True):
    """Persistent record of a chat conversation session.

    Each conversation_id from the HTTP layer maps to one row here. The title
    is auto-populated from the first user message when not supplied explicitly.
    """

    __tablename__ = "conversations"

    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: str = Field(index=True, unique=True, min_length=1)
    title: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class ChatMessageRecord(SQLModel, table=True):
    """One message turn within a conversation.

    role is one of: user, assistant, tool (following OpenAI convention).
    tool_calls_json stores the raw JSON of tool calls when role=assistant
    had tool invocations; this lets the history be replayed in full fidelity.
    """

    __tablename__ = "chat_messages"

    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: str = Field(index=True, min_length=1, foreign_key="conversations.conversation_id")
    role: str = Field(min_length=1)
    content: str = Field(default="")
    tool_calls_json: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=_utcnow)
