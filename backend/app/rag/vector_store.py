import json
import math
from pathlib import Path

from pydantic import BaseModel, Field

from app.core.exceptions import ToolError
from app.rag.schemas import CodeChunk, RetrievedChunk


class StoredVector(BaseModel):
    """Persisted vector plus the source chunk it represents."""

    embedding: list[float]
    chunk: CodeChunk


class VectorStore:
    """Small persistent vector store for Phase 2 RAG.

    The store keeps vectors and metadata in memory while the app is running and
    can persist the full index to JSON. The scoring path uses cosine similarity;
    vectors from `LocalHashEmbeddingClient` are already normalized, but cosine
    is computed defensively so OpenAI vectors work as well.
    """

    def __init__(self) -> None:
        self._items: list[StoredVector] = []

    @property
    def size(self) -> int:
        return len(self._items)

    def clear(self) -> None:
        self._items.clear()

    def add(self, chunks: list[CodeChunk], embeddings: list[list[float]]) -> None:
        if len(chunks) != len(embeddings):
            raise ToolError("Chunks and embeddings length mismatch")
        for chunk, embedding in zip(chunks, embeddings):
            if not embedding:
                raise ToolError("Embedding vector cannot be empty")
            self._items.append(StoredVector(embedding=embedding, chunk=chunk))

    def search(self, query_embedding: list[float], top_k: int = 5) -> list[RetrievedChunk]:
        if top_k < 1:
            raise ToolError("top_k must be greater than 0")
        if not query_embedding:
            raise ToolError("Query embedding cannot be empty")

        scored: list[RetrievedChunk] = []
        for item in self._items:
            score = _cosine_similarity(query_embedding, item.embedding)
            scored.append(
                RetrievedChunk(
                    file_path=item.chunk.file_path,
                    start_line=item.chunk.start_line,
                    end_line=item.chunk.end_line,
                    content=item.chunk.content,
                    score=score,
                )
            )
        return sorted(scored, key=lambda chunk: chunk.score, reverse=True)[:top_k]

    def save(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = [item.model_dump() for item in self._items]
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "VectorStore":
        source = Path(path)
        store = cls()
        if not source.exists():
            return store
        payload = json.loads(source.read_text(encoding="utf-8"))
        store._items = [StoredVector.model_validate(item) for item in payload]
        return store


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        raise ToolError("Embedding dimensions do not match")
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)
