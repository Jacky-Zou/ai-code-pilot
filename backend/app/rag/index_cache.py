import hashlib
import threading
import time
from pathlib import Path

from app.core.logger import get_logger

logger = get_logger(__name__)

# Projects are re-indexed if this many seconds have passed since the last index.
# Developers rarely change thousands of files mid-session; 5 minutes is a safe TTL.
_DEFAULT_TTL_SECONDS = 300


class IndexCache:
    """Thread-safe per-project index freshness tracker.

    Maps a canonical project path key to the timestamp of its last successful
    indexing. RetrieveCodeTool checks this before deciding whether to rebuild
    the vector index. A short TTL keeps results fresh during active editing
    without re-indexing on every query.
    """

    def __init__(self, ttl_seconds: float = _DEFAULT_TTL_SECONDS) -> None:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        self._ttl = ttl_seconds
        self._timestamps: dict[str, float] = {}
        self._lock = threading.Lock()

    def is_fresh(self, project_key: str) -> bool:
        with self._lock:
            ts = self._timestamps.get(project_key)
            return ts is not None and (time.monotonic() - ts) < self._ttl

    def mark_indexed(self, project_key: str) -> None:
        with self._lock:
            self._timestamps[project_key] = time.monotonic()
            logger.debug("Index cache updated project_key=%s", project_key)

    def invalidate(self, project_key: str) -> None:
        with self._lock:
            self._timestamps.pop(project_key, None)


def project_key(project_path: str) -> str:
    """Derive a stable, filesystem-safe key from a project path.

    Used both as a Chroma collection name suffix and a cache dict key.
    SHA-256 keeps it short and avoids path-separator / length issues on
    Windows. The folder_name prefix aids human readability in Chroma storage.
    """

    normalized = Path(project_path).resolve().as_posix().lower()
    digest = hashlib.sha256(normalized.encode()).hexdigest()[:12]
    folder_name = Path(project_path).name[:20].replace(" ", "_")
    return f"acp_{folder_name}_{digest}"


_cache: IndexCache | None = None
_cache_lock = threading.Lock()


def get_index_cache() -> IndexCache:
    """Return the process-wide index cache as a lazy singleton."""

    global _cache
    if _cache is None:
        with _cache_lock:
            if _cache is None:
                _cache = IndexCache()
    return _cache
