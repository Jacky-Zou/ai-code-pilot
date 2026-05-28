from abc import ABC, abstractmethod
from typing import Any


class BaseLLMProvider(ABC):
    provider_name: str

    @abstractmethod
    def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        **kwargs: Any,
    ) -> str:
        raise NotImplementedError
