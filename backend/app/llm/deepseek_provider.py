from typing import Any

from app.core.config import Settings, get_settings
from app.core.exceptions import ConfigurationError
from app.llm.base import BaseLLMProvider
from app.llm.client import extract_chat_content, extract_chat_result, post_chat_completion
from app.llm.schemas import ChatResult

# DeepSeek's chat completions API is fully OpenAI-compatible, including the
# tool_calls / function-calling schema. The same auto-dispatch value applies.
_TOOL_CHOICE_AUTO = "auto"


class DeepSeekProvider(BaseLLMProvider):
    provider_name = "deepseek"

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def chat(
        self,
        messages: list[dict[str, Any]],
        model: str | None = None,
        **kwargs: Any,
    ) -> str:
        self._require_key()
        data = post_chat_completion(
            base_url=self.settings.deepseek_base_url,
            api_key=self.settings.deepseek_api_key,  # type: ignore[arg-type]
            model=model or self.settings.deepseek_model,
            messages=messages,
            **kwargs,
        )
        return extract_chat_content(data)

    def chat_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        model: str | None = None,
    ) -> ChatResult:
        """Call the DeepSeek chat completions endpoint with tool definitions.

        DeepSeek's API is fully OpenAI function-calling compatible, so the
        same wrapper format (type=function) and tool_choice=auto apply.
        """

        self._require_key()
        openai_tools = [{"type": "function", "function": t} for t in tools]
        data = post_chat_completion(
            base_url=self.settings.deepseek_base_url,
            api_key=self.settings.deepseek_api_key,  # type: ignore[arg-type]
            model=model or self.settings.deepseek_model,
            messages=messages,
            tools=openai_tools,
            tool_choice=_TOOL_CHOICE_AUTO,
        )
        return extract_chat_result(data)

    def _require_key(self) -> None:
        if not self.settings.deepseek_api_key:
            raise ConfigurationError("DEEPSEEK_API_KEY is required to use the DeepSeek provider")
