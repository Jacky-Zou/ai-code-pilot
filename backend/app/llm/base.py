from abc import ABC, abstractmethod
from typing import Any

from app.llm.schemas import ChatResult


class BaseLLMProvider(ABC):
    provider_name: str

    @abstractmethod
    def chat(
        self,
        messages: list[dict[str, Any]],
        model: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Plain text chat completion.

        Used as the fallback path when tool definitions are absent or when the
        provider does not implement chat_with_tools. Returns the raw text
        content of the model's reply.
        """

        raise NotImplementedError

    @abstractmethod
    def chat_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        model: str | None = None,
    ) -> ChatResult:
        """Chat completion with tool definitions in OpenAI function-calling format.

        `tools` is a list of JSON Schema dicts exactly as produced by
        BaseTool.schema(). Returns a ChatResult with either tool_calls (model
        wants to invoke a tool) or a final content string (model is done).

        Providers that do not natively support function calling should raise
        NotImplementedError so the executor can fall back to the text protocol.
        Providers that do support it must return ChatResult in all cases and
        raise LLMProviderError on HTTP/network failure.
        """

        raise NotImplementedError
