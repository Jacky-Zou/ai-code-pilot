from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

from app.core.config import get_settings
from app.core.logger import get_logger

logger = get_logger(__name__)

_engine = None


def _get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        db_url = settings.database_url
        connect_args = {}
        if db_url.startswith("sqlite"):
            connect_args = {"check_same_thread": False}
        _engine = create_engine(
            db_url,
            connect_args=connect_args,
            echo=False,
        )
        # WAL mode improves concurrent read performance for SQLite
        if db_url.startswith("sqlite"):
            with _engine.connect() as conn:
                conn.exec_driver_sql("PRAGMA journal_mode=WAL")
        logger.info("Database engine initialized url=%s", db_url)
    return _engine


def init_db() -> None:
    """Create all tables. Called once at application startup."""
    from app.db import models as _  # noqa: F401 — ensure models are registered

    SQLModel.metadata.create_all(_get_engine())
    logger.info("Database tables initialized")


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a per-request database session."""
    with Session(_get_engine()) as session:
        yield session
