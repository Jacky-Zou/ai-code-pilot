import pytest

from app.llm.base import BaseLLMProvider
from app.llm.schemas import LLMResponse, Message


def test_base_provider_is_abstract() -> None:
    with pytest.raises(TypeError):
        BaseLLMProvider()  # type: ignore[abstract]


class DummyProvider(BaseLLMProvider):
    provider_name = "dummy"

    def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        **kwargs: object,
    ) -> str:
        return messages[-1]["content"]

    def chat_with_tools(self, messages, tools, model=None):  # type: ignore[override]
        raise NotImplementedError


def test_provider_interface() -> None:
    provider = DummyProvider()

    assert provider.chat([{"role": "user", "content": "hello"}]) == "hello"


def test_message_to_api_dict() -> None:
    message = Message(role="user", content="hello")

    assert message.to_api_dict() == {"role": "user", "content": "hello"}


def test_llm_response_schema() -> None:
    response = LLMResponse(content="answer", provider="openai", model="gpt-5.2")

    assert response.content == "answer"
    assert response.raw is None
