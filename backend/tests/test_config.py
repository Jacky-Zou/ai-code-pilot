from pathlib import Path

import pytest

from app.core.config import Settings, get_settings


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in (
        "APP_NAME",
        "APP_ENV",
        "LOG_LEVEL",
        "LLM_PROVIDER",
        "LLM_MODEL",
        "OPENAI_API_KEY",
        "OPENAI_BASE_URL",
        "OPENAI_MODEL",
        "DEEPSEEK_API_KEY",
        "DEEPSEEK_BASE_URL",
        "DEEPSEEK_MODEL",
        "EMBEDDING_PROVIDER",
        "EMBEDDING_MODEL",
        "VECTOR_STORE_PATH",
    ):
        monkeypatch.delenv(key, raising=False)

    settings = Settings(_env_file=None)

    assert settings.app_name == "AICodePilot"
    assert settings.app_env == "development"
    assert settings.log_level == "INFO"
    assert settings.llm_provider == "openai"
    assert settings.openai_model == "gpt-4o-mini"
    assert settings.deepseek_model == "deepseek-chat"
    assert settings.embedding_model == "text-embedding-3-small"
    assert settings.vector_store_path == Path("data/vector_store")


def test_settings_reads_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_NAME", "CustomPilot")
    monkeypatch.setenv("LOG_LEVEL", "debug")
    monkeypatch.setenv("LLM_PROVIDER", "DeepSeek")
    monkeypatch.setenv("DEEPSEEK_MODEL", "deepseek-reasoner")
    monkeypatch.setenv("VECTOR_STORE_PATH", "./tmp/vectors")

    settings = Settings(_env_file=None)

    assert settings.app_name == "CustomPilot"
    assert settings.log_level == "DEBUG"
    assert settings.llm_provider == "deepseek"
    assert settings.default_model_for_provider() == "deepseek-reasoner"
    assert settings.vector_store_path == Path("tmp/vectors")


def test_default_model_for_provider() -> None:
    settings = Settings(_env_file=None)

    assert settings.default_model_for_provider("openai") == "gpt-4o-mini"
    assert settings.default_model_for_provider("deepseek") == "deepseek-chat"


def test_default_model_rejects_unknown_provider() -> None:
    settings = Settings(_env_file=None)

    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        settings.default_model_for_provider("unknown")
