import hashlib
import math
import re
from abc import ABC, abstractmethod
from typing import Any

import httpx

from app.core.config import Settings, get_settings
from app.core.exceptions import ConfigurationError, LLMProviderError, UnsupportedProviderError

_TOKEN_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|[\u4e00-\u9fff]+")


class BaseEmbeddingClient(ABC):
    """Common interface for all embedding providers."""

    provider_name: str

    @abstractmethod
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError

    def embed_query(self, query: str) -> list[float]:
        return self.embed_texts([query])[0]


class OpenAIEmbeddingClient(BaseEmbeddingClient):
    """OpenAI-compatible embedding client.

    The class fails before making an HTTP request when `OPENAI_API_KEY` is not
    configured. This gives users a clear setup error instead of a confusing
    provider-side authentication failure.
    """

    provider_name = "openai"

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not self.settings.openai_api_key:
            raise ConfigurationError("OPENAI_API_KEY is required to use OpenAI embeddings")
        if not texts:
            return []

        url = f"{self.settings.openai_base_url.rstrip('/')}/embeddings"
        payload = {"model": self.settings.embedding_model, "input": texts}
        headers = {
            "Authorization": f"Bearer {self.settings.openai_api_key}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as exc:
            raise LLMProviderError(f"Embedding provider returned HTTP {exc.response.status_code}: {exc.response.text}") from exc
        except httpx.RequestError as exc:
            raise LLMProviderError(f"Embedding provider request failed: {exc}") from exc

        return self._extract_embeddings(data)

    def _extract_embeddings(self, data: dict[str, Any]) -> list[list[float]]:
        try:
            rows = sorted(data["data"], key=lambda item: item["index"])
            return [list(row["embedding"]) for row in rows]
        except (KeyError, TypeError) as exc:
            raise LLMProviderError("Embedding provider response does not contain embeddings") from exc


class LocalHashEmbeddingClient(BaseEmbeddingClient):
    """Deterministic local embedding for tests and offline demos.

    This is not a replacement for model embeddings. It hashes lexical tokens
    into a fixed-size vector so retrieval can be validated without network
    access or API keys. The vector is normalized, which keeps cosine scoring
    stable across snippets of different length.
    """

    provider_name = "local"

    def __init__(self, dimension: int = 256) -> None:
        if dimension < 8:
            raise ValueError("dimension must be at least 8")
        self.dimension = dimension

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        tokens = _TOKEN_PATTERN.findall(text.lower())
        for token in tokens:
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]


def create_embedding_client(provider_name: str | None = None, settings: Settings | None = None) -> BaseEmbeddingClient:
    resolved_settings = settings or get_settings()
    provider = (provider_name or resolved_settings.embedding_provider).strip().lower()
    if provider == "openai":
        return OpenAIEmbeddingClient(settings=resolved_settings)
    if provider == "local":
        return LocalHashEmbeddingClient()
    raise UnsupportedProviderError(f"Unsupported embedding provider: {provider}")
