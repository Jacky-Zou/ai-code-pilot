import json
import math
import uuid
from pathlib import Path
from typing import Any, Protocol, cast

from pydantic import BaseModel

from app.core.exceptions import ToolError
from app.rag.schemas import CodeChunk, RetrievedChunk


class BaseVectorStore(Protocol):
    """Minimal vector store contract used by the retriever.

    Keeping this protocol narrow lets the project swap storage engines without
    changing Agent or Retriever logic. Chroma is the production Phase 2 backend;
    the JSON store remains useful for deterministic unit tests and debugging.
    """

    @property
    def size(self) -> int:
        raise NotImplementedError

    def clear(self) -> None:
        raise NotImplementedError

    def add(self, chunks: list[CodeChunk], embeddings: list[list[float]]) -> None:
        raise NotImplementedError

    def search(self, query_embedding: list[float], top_k: int = 5) -> list[RetrievedChunk]:
        raise NotImplementedError

    def save(self, path: str | Path) -> None:
        raise NotImplementedError


class StoredVector(BaseModel):
    """Persisted vector plus the source chunk it represents."""

    embedding: list[float]
    chunk: CodeChunk


class JsonVectorStore:
    """Small JSON vector store used for tests and local fallback.

    It keeps vectors and metadata in memory while the app is running and can
    persist the full index to JSON. Chroma is the default runtime backend, but
    this class gives tests a dependency-light store with exactly the same public
    contract.
    """

    def __init__(self) -> None:
        self._items: list[StoredVector] = []

    @property
    def size(self) -> int:
        return len(self._items)

    def clear(self) -> None:
        self._items.clear()

    def add(self, chunks: list[CodeChunk], embeddings: list[list[float]]) -> None:
        _validate_add_inputs(chunks, embeddings)
        for chunk, embedding in zip(chunks, embeddings):
            self._items.append(StoredVector(embedding=embedding, chunk=chunk))

    def search(self, query_embedding: list[float], top_k: int = 5) -> list[RetrievedChunk]:
        _validate_search_inputs(query_embedding, top_k)
        scored: list[RetrievedChunk] = []
        for item in self._items:
            score = _cosine_similarity(query_embedding, item.embedding)
            scored.append(_to_retrieved_chunk(item.chunk, score))
        return sorted(scored, key=lambda chunk: chunk.score, reverse=True)[:top_k]

    def save(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = [item.model_dump() for item in self._items]
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "JsonVectorStore":
        source = Path(path)
        store = cls()
        if not source.exists():
            return store
        payload = json.loads(source.read_text(encoding="utf-8"))
        store._items = [StoredVector.model_validate(item) for item in payload]
        return store


class ChromaVectorStore:
    """Chroma-backed persistent vector store for code chunks.

    Chroma stores vectors, documents, and metadata on disk under
    `persist_directory`. AICodePilot supplies embeddings itself, so Chroma is
    used purely as the vector database and does not call external embedding
    services. Search returns cosine-like similarity by converting Chroma's
    distance value into a higher-is-better score.
    """

    def __init__(self, persist_directory: str | Path, collection_name: str = "aicodepilot_code") -> None:
        self.persist_directory = Path(persist_directory)
        self.collection_name = collection_name
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        try:
            import chromadb
        except ImportError as exc:
            raise ToolError("chromadb is required for ChromaVectorStore. Install backend requirements first.") from exc

        self._client = chromadb.PersistentClient(path=str(self.persist_directory))
        self._collection = self._client.get_or_create_collection(name=collection_name, metadata={"hnsw:space": "cosine"})

    @property
    def size(self) -> int:
        return int(self._collection.count())

    def clear(self) -> None:
        try:
            self._client.delete_collection(self.collection_name)
        except Exception:
            pass
        self._collection = self._client.get_or_create_collection(name=self.collection_name, metadata={"hnsw:space": "cosine"})

    def add(self, chunks: list[CodeChunk], embeddings: list[list[float]]) -> None:
        _validate_add_inputs(chunks, embeddings)
        if not chunks:
            return

        ids = [str(uuid.uuid4()) for _ in chunks]
        documents = [chunk.content for chunk in chunks]
        metadatas: list[dict[str, str | int]] = [
            {
                "file_path": chunk.file_path,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
            }
            for chunk in chunks
        ]
        self._collection.add(ids=ids, embeddings=cast(Any, embeddings), documents=documents, metadatas=cast(Any, metadatas))

    def search(self, query_embedding: list[float], top_k: int = 5) -> list[RetrievedChunk]:
        _validate_search_inputs(query_embedding, top_k)
        if self.size == 0:
            return []

        result = cast(
            dict[str, Any], self._collection.query(query_embeddings=cast(Any, [query_embedding]), n_results=min(top_k, self.size))
        )
        documents = result.get("documents") or [[]]
        metadatas = result.get("metadatas") or [[]]
        distances = result.get("distances") or [[]]

        chunks: list[RetrievedChunk] = []
        for document, metadata, distance in zip(documents[0], metadatas[0], distances[0]):
            score = 1.0 - float(distance)
            chunks.append(
                RetrievedChunk(
                    file_path=str(metadata["file_path"]),
                    start_line=int(metadata["start_line"]),
                    end_line=int(metadata["end_line"]),
                    content=str(document),
                    score=score,
                )
            )
        return chunks

    def save(self, path: str | Path) -> None:
        # Chroma's PersistentClient writes changes to its persist directory as
        # records are added. The method exists to satisfy the shared contract.
        Path(path).mkdir(parents=True, exist_ok=True)

    @classmethod
    def load(cls, path: str | Path, collection_name: str = "aicodepilot_code") -> "ChromaVectorStore":
        return cls(persist_directory=path, collection_name=collection_name)


# Backward-compatible alias used by older tests/imports.
VectorStore = JsonVectorStore


def create_vector_store(
    backend: str = "chroma",
    persist_directory: str | Path = "./data/vector_store",
    collection_name: str = "aicodepilot_code",
) -> BaseVectorStore:
    normalized = backend.strip().lower()
    if normalized == "chroma":
        return ChromaVectorStore(persist_directory=persist_directory, collection_name=collection_name)
    if normalized in {"json", "memory"}:
        return JsonVectorStore()
    raise ToolError(f"Unsupported vector store backend: {backend}")


def load_vector_store(
    backend: str = "chroma",
    path: str | Path = "./data/vector_store",
    collection_name: str = "aicodepilot_code",
) -> BaseVectorStore:
    normalized = backend.strip().lower()
    if normalized == "chroma":
        return ChromaVectorStore.load(path, collection_name=collection_name)
    if normalized in {"json", "memory"}:
        return JsonVectorStore.load(path)
    raise ToolError(f"Unsupported vector store backend: {backend}")


def _validate_add_inputs(chunks: list[CodeChunk], embeddings: list[list[float]]) -> None:
    if len(chunks) != len(embeddings):
        raise ToolError("Chunks and embeddings length mismatch")
    for embedding in embeddings:
        if not embedding:
            raise ToolError("Embedding vector cannot be empty")


def _validate_search_inputs(query_embedding: list[float], top_k: int) -> None:
    if top_k < 1:
        raise ToolError("top_k must be greater than 0")
    if not query_embedding:
        raise ToolError("Query embedding cannot be empty")


def _to_retrieved_chunk(chunk: CodeChunk, score: float) -> RetrievedChunk:
    return RetrievedChunk(
        file_path=chunk.file_path,
        start_line=chunk.start_line,
        end_line=chunk.end_line,
        content=chunk.content,
        score=score,
    )


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        raise ToolError("Embedding dimensions do not match")
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)
