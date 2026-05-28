from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class BaseTool(ABC):
    name: str
    description: str
    args_schema: type[BaseModel]

    def validate_args(self, arguments: dict[str, Any]) -> BaseModel:
        return self.args_schema.model_validate(arguments)

    def schema(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.args_schema.model_json_schema(),
        }

    @abstractmethod
    def run(self, **kwargs: Any) -> Any:
        raise NotImplementedError
