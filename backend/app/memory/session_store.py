import threading
import time
from dataclasses import dataclass, field

from app.core.logger import get_logger
from app.memory.conversation_memory import ConversationMemory

logger = get_logger(__name__)

# A session is evicted after this many seconds of inactivity. Local developer
# assistant sessions are short-lived; unbounded retention would leak memory and
# keep stale project context alive across unrelated tasks.
_DEFAULT_TTL_SECONDS = 60 * 60
# Hard cap on concurrent sessions so a misbehaving client cannot exhaust memory.
_DEFAULT_MAX_SESSIONS = 500


@dataclass
class _SessionEntry:
    memory: ConversationMemory
    last_access: float = field(default_factory=time.monotonic)


class SessionStore:
    """Thread-safe registry mapping conversation_id -> ConversationMemory.

    The chat API is stateless at the HTTP layer, so multi-turn context must be
    rebuilt server-side from a stable conversation id. This store keeps each
    conversation's bounded memory alive between requests, evicts idle sessions
    on a TTL, and caps total sessions to bound memory use. A single lock guards
    all mutations because ConversationMemory itself is not thread-safe and the
    same conversation_id may be hit concurrently by retries or double-submits.
    """

    def __init__(
        self,
        ttl_seconds: float = _DEFAULT_TTL_SECONDS,
        max_sessions: int = _DEFAULT_MAX_SESSIONS,
        max_turns: int = 8,
    ) -> None:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        if max_sessions < 1:
            raise ValueError("max_sessions must be at least 1")
        self._ttl_seconds = ttl_seconds
        self._max_sessions = max_sessions
        self._max_turns = max_turns
        self._entries: dict[str, _SessionEntry] = {}
        self._lock = threading.Lock()

    def get_or_create(self, conversation_id: str) -> ConversationMemory:
        cleaned = conversation_id.strip()
        if not cleaned:
            raise ValueError("conversation_id cannot be empty")

        now = time.monotonic()
        with self._lock:
            self._evict_expired_locked(now)
            entry = self._entries.get(cleaned)
            if entry is None:
                self._enforce_capacity_locked()
                entry = _SessionEntry(
                    memory=ConversationMemory(max_turns=self._max_turns, conversation_id=cleaned)
                )
                self._entries[cleaned] = entry
                logger.info(
                    "Session created conversation_id=%s total_sessions=%s",
                    cleaned,
                    len(self._entries),
                )
            entry.last_access = now
            return entry.memory

    def drop(self, conversation_id: str) -> None:
        with self._lock:
            if self._entries.pop(conversation_id.strip(), None) is not None:
                logger.info("Session dropped conversation_id=%s", conversation_id)

    def active_count(self) -> int:
        with self._lock:
            return len(self._entries)

    def _evict_expired_locked(self, now: float) -> None:
        expired = [
            key
            for key, entry in self._entries.items()
            if now - entry.last_access > self._ttl_seconds
        ]
        for key in expired:
            del self._entries[key]
        if expired:
            logger.info("Evicted idle sessions count=%s", len(expired))

    def _enforce_capacity_locked(self) -> None:
        # Evict the least-recently-used session when at capacity. This is O(n)
        # but n is bounded by max_sessions and creation is infrequent relative
        # to per-message traffic, so a heap is unnecessary complexity here.
        while len(self._entries) >= self._max_sessions:
            oldest_key = min(self._entries, key=lambda key: self._entries[key].last_access)
            del self._entries[oldest_key]
            logger.warning(
                "Session capacity reached, evicted LRU conversation_id=%s", oldest_key
            )


_session_store: SessionStore | None = None
_store_lock = threading.Lock()


def get_session_store() -> SessionStore:
    """Return the process-wide session store as a lazy singleton."""

    global _session_store
    if _session_store is None:
        with _store_lock:
            if _session_store is None:
                _session_store = SessionStore()
    return _session_store
