from pathlib import Path

import pytest
from pydantic import ValidationError

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
        "VECTOR_STORE_BACKEND",
        "CORS_ALLOWED_ORIGINS",
    ):
        monkeypatch.delenv(key, raising=False)

    settings = Settings(_env_file=None)

    assert settings.app_name == "AICodePilot"
    assert settings.app_env == "development"
    assert settings.log_level == "INFO"
    assert settings.llm_provider == "openai"
    assert settings.openai_model == "gpt-5.2"
    assert settings.deepseek_model == "deepseek-v4-pro"
    assert settings.embedding_model == "text-embedding-3-small"
    assert settings.vector_store_path == Path("data/vector_store")
    assert settings.vector_store_backend == "chroma"
    assert settings.cors_allowed_origin_list == ["http://localhost:3000", "http://127.0.0.1:3000"]


def test_settings_reads_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_NAME", "CustomPilot")
    monkeypatch.setenv("LOG_LEVEL", "debug")
    monkeypatch.setenv("LLM_PROVIDER", "DeepSeek")
    monkeypatch.setenv("LLM_MODEL", "")
    monkeypatch.setenv("DEEPSEEK_MODEL", "deepseek-reasoner")
    monkeypatch.setenv("OPENAI_BASE_URL", " https://proxy.example.com/v1/ ")
    monkeypatch.setenv("EMBEDDING_PROVIDER", "LOCAL")
    monkeypatch.setenv("VECTOR_STORE_PATH", "./tmp/vectors")
    monkeypatch.setenv("VECTOR_STORE_BACKEND", "JSON")
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000, https://example.com/")

    settings = Settings(_env_file=None)

    assert settings.app_name == "CustomPilot"
    assert settings.log_level == "DEBUG"
    assert settings.llm_provider == "deepseek"
    assert settings.llm_model == "deepseek-reasoner"
    assert settings.default_model_for_provider() == "deepseek-reasoner"
    assert settings.openai_base_url == "https://proxy.example.com/v1"
    assert settings.embedding_provider == "local"
    assert settings.vector_store_path == Path("tmp/vectors")
    assert settings.vector_store_backend == "json"
    assert settings.cors_allowed_origin_list == ["http://localhost:3000", "https://example.com"]


def test_default_model_for_provider() -> None:
    settings = Settings(_env_file=None)

    assert settings.default_model_for_provider("openai") == "gpt-5.2"
    assert settings.default_model_for_provider("deepseek") == "deepseek-v4-pro"


def test_default_model_rejects_unknown_provider() -> None:
    settings = Settings(_env_file=None)

    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        settings.default_model_for_provider("unknown")


@pytest.mark.parametrize(
    ("env_name", "env_value", "message"),
    [
        ("LLM_PROVIDER", "unknown", "Unsupported LLM_PROVIDER"),
        ("EMBEDDING_PROVIDER", "unknown", "Unsupported EMBEDDING_PROVIDER"),
        ("VECTOR_STORE_BACKEND", "sqlite", "Unsupported VECTOR_STORE_BACKEND"),
        ("LOG_LEVEL", "verbose", "Unsupported LOG_LEVEL"),
        ("CORS_ALLOWED_ORIGINS", "localhost:3000", "CORS origins must start"),
    ],
)
def test_settings_rejects_unsupported_runtime_choices(
    monkeypatch: pytest.MonkeyPatch,
    env_name: str,
    env_value: str,
    message: str,
) -> None:
    monkeypatch.setenv(env_name, env_value)

    with pytest.raises(ValidationError, match=message):
        Settings(_env_file=None)


def test_settings_rejects_invalid_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_BASE_URL", "api.openai.test/v1")

    with pytest.raises(ValidationError, match="base URL must start"):
        Settings(_env_file=None)


def test_settings_rejects_blank_required_provider_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_MODEL", " ")

    with pytest.raises(ValidationError, match="model name cannot be empty"):
        Settings(_env_file=None)
