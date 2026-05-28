import pytest

from app.core.config import Settings
from app.core.exceptions import UnsupportedProviderError
from app.llm.deepseek_provider import DeepSeekProvider
from app.llm.factory import LLMProviderFactory
from app.llm.openai_provider import OpenAIProvider


def test_factory_creates_openai_provider() -> None:
    provider = LLMProviderFactory.create("openai", settings=Settings(_env_file=None))

    assert isinstance(provider, OpenAIProvider)


def test_factory_creates_deepseek_provider() -> None:
    provider = LLMProviderFactory.create("deepseek", settings=Settings(_env_file=None))

    assert isinstance(provider, DeepSeekProvider)


def test_factory_uses_default_provider() -> None:
    settings = Settings(LLM_PROVIDER="deepseek", _env_file=None)

    provider = LLMProviderFactory.create(settings=settings)

    assert isinstance(provider, DeepSeekProvider)


def test_factory_rejects_unsupported_provider() -> None:
    with pytest.raises(UnsupportedProviderError, match="Unsupported LLM provider"):
        LLMProviderFactory.create("unknown", settings=Settings(_env_file=None))
