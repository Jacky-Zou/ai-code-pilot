from typing import Any

from app.core.config import Settings, get_settings
from app.core.exceptions import ConfigurationError
from app.llm.base import BaseLLMProvider
from app.llm.client import extract_chat_content, post_chat_completion


class DeepSeekProvider(BaseLLMProvider):
    provider_name = "deepseek"

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        **kwargs: Any,
    ) -> str:
        if not self.settings.deepseek_api_key:
            raise ConfigurationError("DEEPSEEK_API_KEY is required to use the DeepSeek provider")

        selected_model = model or self.settings.deepseek_model
        data = post_chat_completion(
            base_url=self.settings.deepseek_base_url,
            api_key=self.settings.deepseek_api_key,
            model=selected_model,
            messages=messages,
            **kwargs,
        )
        return extract_chat_content(data)
