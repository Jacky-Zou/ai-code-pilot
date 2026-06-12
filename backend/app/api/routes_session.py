from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db.engine import get_session
from app.db.models import ChatMessageRecord
from app.db.repository import ConversationRepository
from app.memory.session_store import get_session_store

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.get("/{conversation_id}/messages", response_model=list[ChatMessageRecord])
def get_messages(
    conversation_id: str,
    limit: int = 16,
    db: Session = Depends(get_session),
) -> list[ChatMessageRecord]:
    """Return recent messages for a conversation."""
    repo = ConversationRepository(db)
    return repo.recent_messages(conversation_id, limit=limit)


@router.delete("/{conversation_id}", status_code=204)
def delete_session(
    conversation_id: str,
    db: Session = Depends(get_session),
) -> None:
    """Delete a conversation and its messages from DB and in-memory session store."""
    repo = ConversationRepository(db)
    repo.delete_conversation(conversation_id)
    get_session_store().drop(conversation_id)
