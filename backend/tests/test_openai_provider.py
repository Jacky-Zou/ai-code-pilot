import pytest

from app.core.config import Settings
from app.core.exceptions import ConfigurationError
from app.llm import openai_provider
from app.llm.openai_provider import OpenAIProvider


def test_openai_provider_requires_api_key() -> None:
    settings = Settings(OPENAI_API_KEY=None, _env_file=None)
    provider = OpenAIProvider(settings=settings)

    with pytest.raises(ConfigurationError, match="OPENAI_API_KEY"):
        provider.chat([{"role": "user", "content": "hello"}])


def test_openai_provider_uses_model_override(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_post_chat_completion(**kwargs: object) -> dict[str, object]:
        captured.update(kwargs)
        return {"choices": [{"message": {"content": "ok"}}]}

    monkeypatch.setattr(openai_provider, "post_chat_completion", fake_post_chat_completion)
    settings = Settings(OPENAI_API_KEY="test-key", OPENAI_MODEL="default-model", _env_file=None)
    provider = OpenAIProvider(settings=settings)

    answer = provider.chat([{"role": "user", "content": "hello"}], model="override-model")

    assert answer == "ok"
    assert captured["model"] == "override-model"
    assert captured["api_key"] == "test-key"
