from datetime import datetime, timezone

from sqlmodel import Session, select

from app.core.logger import get_logger
from app.db.models import ChatMessageRecord, Conversation

logger = get_logger(__name__)


class ConversationRepository:
    """Data-access layer for conversations and their message history."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def ensure_conversation(self, conversation_id: str, title: str | None = None) -> Conversation:
        """Return the existing conversation or create a new one."""
        existing = self._session.exec(select(Conversation).where(Conversation.conversation_id == conversation_id)).first()
        if existing is not None:
            return existing
        conv = Conversation(conversation_id=conversation_id, title=title)
        self._session.add(conv)
        self._session.commit()
        self._session.refresh(conv)
        logger.info("Conversation created conversation_id=%s", conversation_id)
        return conv

    def append_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        tool_calls_json: str | None = None,
    ) -> ChatMessageRecord:
        """Append one message to the conversation and flush within the caller's transaction."""
        record = ChatMessageRecord(
            conversation_id=conversation_id,
            role=role,
            content=content,
            tool_calls_json=tool_calls_json,
        )
        self._session.add(record)
        # Update parent conversation timestamp
        conv = self._session.exec(select(Conversation).where(Conversation.conversation_id == conversation_id)).first()
        if conv is not None:
            conv.updated_at = datetime.now(timezone.utc)
            self._session.add(conv)
        self._session.commit()
        self._session.refresh(record)
        return record

    def recent_messages(self, conversation_id: str, limit: int = 16) -> list[ChatMessageRecord]:
        """Return the most recent messages for a conversation, oldest-first."""
        rows = self._session.exec(
            select(ChatMessageRecord)
            .where(ChatMessageRecord.conversation_id == conversation_id)
            .order_by(ChatMessageRecord.id.desc())  # type: ignore[union-attr]
            .limit(limit)
        ).all()
        return list(reversed(rows))

    def delete_conversation(self, conversation_id: str) -> None:
        """Delete a conversation and all its messages."""
        messages = self._session.exec(select(ChatMessageRecord).where(ChatMessageRecord.conversation_id == conversation_id)).all()
        for msg in messages:
            self._session.delete(msg)
        conv = self._session.exec(select(Conversation).where(Conversation.conversation_id == conversation_id)).first()
        if conv is not None:
            self._session.delete(conv)
        self._session.commit()
        logger.info("Conversation deleted conversation_id=%s", conversation_id)
