from typing import Any

from app.core.config import Settings, get_settings
from app.core.exceptions import ConfigurationError
from app.llm.base import BaseLLMProvider
from app.llm.client import extract_chat_content, post_chat_completion


class OpenAIProvider(BaseLLMProvider):
    provider_name = "openai"

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        **kwargs: Any,
    ) -> str:
        if not self.settings.openai_api_key:
            raise ConfigurationError("OPENAI_API_KEY is required to use the OpenAI provider")

        selected_model = model or self.settings.openai_model
        data = post_chat_completion(
            base_url=self.settings.openai_base_url,
            api_key=self.settings.openai_api_key,
            model=selected_model,
            messages=messages,
            **kwargs,
        )
        return extract_chat_content(data)
