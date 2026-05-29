import logging

import pytest

from app.core.config import get_settings
from app.core.logger import configure_logging, get_logger, reset_logging_for_tests


@pytest.fixture(autouse=True)
def reset_logger_state() -> None:
    get_settings.cache_clear()
    reset_logging_for_tests()
    yield
    reset_logging_for_tests()
    get_settings.cache_clear()


def test_configure_logging_uses_env_level(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOG_LEVEL", "debug")

    configure_logging(force=True)

    assert logging.getLogger().level == logging.DEBUG


def test_get_logger_emits_project_format(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("LOG_LEVEL", "info")

    logger = get_logger("aicodepilot.test")
    logger.info("hello logging")

    captured = capsys.readouterr()
    assert "INFO | aicodepilot.test | hello logging" in captured.out


def test_configure_logging_can_rebuild_handlers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOG_LEVEL", "info")
    configure_logging(force=True)
    assert logging.getLogger().level == logging.INFO

    get_settings.cache_clear()
    monkeypatch.setenv("LOG_LEVEL", "error")
    configure_logging(force=True)

    assert logging.getLogger().level == logging.ERROR
