import pytest

from app.core.config import Settings
from app.core.exceptions import ConfigurationError
from app.llm import deepseek_provider
from app.llm.deepseek_provider import DeepSeekProvider


def test_deepseek_provider_requires_api_key() -> None:
    settings = Settings(DEEPSEEK_API_KEY=None, _env_file=None)
    provider = DeepSeekProvider(settings=settings)

    with pytest.raises(ConfigurationError, match="DEEPSEEK_API_KEY"):
        provider.chat([{"role": "user", "content": "hello"}])


def test_deepseek_provider_uses_default_model(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_post_chat_completion(**kwargs: object) -> dict[str, object]:
        captured.update(kwargs)
        return {"choices": [{"message": {"content": "deepseek ok"}}]}

    monkeypatch.setattr(deepseek_provider, "post_chat_completion", fake_post_chat_completion)
    settings = Settings(DEEPSEEK_API_KEY="test-key", DEEPSEEK_MODEL="deepseek-v4-pro", _env_file=None)
    provider = DeepSeekProvider(settings=settings)

    answer = provider.chat([{"role": "user", "content": "hello"}])

    assert answer == "deepseek ok"
    assert captured["model"] == "deepseek-v4-pro"
    assert captured["api_key"] == "test-key"
