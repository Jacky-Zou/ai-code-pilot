import pytest

from app.core.config import Settings
from app.core.exceptions import ConfigurationError, UnsupportedProviderError
from app.rag.embeddings import LocalHashEmbeddingClient, OpenAIEmbeddingClient, create_embedding_client


def cosine(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def test_openai_embedding_requires_api_key() -> None:
    client = OpenAIEmbeddingClient(settings=Settings(OPENAI_API_KEY=None, _env_file=None))

    with pytest.raises(ConfigurationError, match="OPENAI_API_KEY"):
        client.embed_texts(["hello"])


def test_local_hash_embedding_is_deterministic() -> None:
    client = LocalHashEmbeddingClient(dimension=32)

    first = client.embed_query("Agent tool registry")
    second = client.embed_query("Agent tool registry")

    assert first == second
    assert len(first) == 32


def test_local_hash_embedding_scores_related_text_higher() -> None:
    client = LocalHashEmbeddingClient(dimension=64)
    query = client.embed_query("agent registry")
    related = client.embed_query("agent registry tool")
    unrelated = client.embed_query("docker compose deployment")

    assert cosine(query, related) > cosine(query, unrelated)


def test_embedding_factory_supports_local() -> None:
    client = create_embedding_client("local", settings=Settings(_env_file=None))

    assert isinstance(client, LocalHashEmbeddingClient)


def test_embedding_factory_rejects_unknown_provider() -> None:
    with pytest.raises(UnsupportedProviderError, match="Unsupported embedding provider"):
        create_embedding_client("unknown", settings=Settings(_env_file=None))
