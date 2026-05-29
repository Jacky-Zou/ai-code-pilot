import logging
import sys

from app.core.config import get_settings

_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_CONFIGURED = False


def configure_logging(force: bool = False) -> None:
    """Configure process-wide logging once with project settings.

    Modules call `get_logger(__name__)` during import, so this function stays
    idempotent. Tests can pass `force=True` after changing env vars to rebuild
    handlers without leaking previous logger state.
    """

    global _CONFIGURED
    settings = get_settings()
    level = getattr(logging, settings.log_level, logging.INFO)
    if _CONFIGURED and not force:
        logging.getLogger().setLevel(level)
        return

    logging.basicConfig(
        level=level,
        format=_LOG_FORMAT,
        datefmt=_DATE_FORMAT,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name)


def reset_logging_for_tests() -> None:
    """Reset logging configuration state for focused logger tests only."""

    global _CONFIGURED
    logging.shutdown()
    logging.getLogger().handlers.clear()
    _CONFIGURED = False
