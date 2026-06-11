from typing import Any

from app.core.config import Settings, get_settings
from app.core.exceptions import ConfigurationError
from app.llm.base import BaseLLMProvider
from app.llm.client import extract_chat_content, extract_chat_result, post_chat_completion
from app.llm.schemas import ChatResult

# OpenAI tool_choice value that lets the model decide freely whether to call a
# tool or produce a final answer. "required" would force a call even when the
# model has enough context to answer directly.
_TOOL_CHOICE_AUTO = "auto"


class OpenAIProvider(BaseLLMProvider):
    provider_name = "openai"

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
            base_url=self.settings.openai_base_url,
            api_key=self.settings.openai_api_key,  # type: ignore[arg-type]
            model=model or self.settings.openai_model,
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
        """Call the OpenAI chat completions endpoint with tool definitions.

        tool_choice="auto" lets the model decide whether to call a tool or
        produce a final answer in a single response. This is the standard
        ReAct-style loop entry: each call either yields tool_calls to execute
        or a content string that becomes the agent's answer.

        BaseTool.schema() returns {"name": ..., "description": ..., "parameters": {...}}.
        OpenAI expects {"type": "function", "function": {same fields}}.
        """

        self._require_key()
        openai_tools = [{"type": "function", "function": t} for t in tools]
        data = post_chat_completion(
            base_url=self.settings.openai_base_url,
            api_key=self.settings.openai_api_key,  # type: ignore[arg-type]
            model=model or self.settings.openai_model,
            messages=messages,
            tools=openai_tools,
            tool_choice=_TOOL_CHOICE_AUTO,
        )
        return extract_chat_result(data)

    def _require_key(self) -> None:
        if not self.settings.openai_api_key:
            raise ConfigurationError("OPENAI_API_KEY is required to use the OpenAI provider")
