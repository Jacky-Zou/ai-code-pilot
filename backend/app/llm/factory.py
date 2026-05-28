from app.core.config import Settings, get_settings
from app.core.exceptions import UnsupportedProviderError
from app.llm.base import BaseLLMProvider
from app.llm.deepseek_provider import DeepSeekProvider
from app.llm.openai_provider import OpenAIProvider


class LLMProviderFactory:
    @staticmethod
    def create(provider_name: str | None = None, settings: Settings | None = None) -> BaseLLMProvider:
        resolved_settings = settings or get_settings()
        provider = (provider_name or resolved_settings.llm_provider).strip().lower()

        if provider == "openai":
            return OpenAIProvider(settings=resolved_settings)
        if provider == "deepseek":
            return DeepSeekProvider(settings=resolved_settings)

        raise UnsupportedProviderError(f"Unsupported LLM provider: {provider}")
