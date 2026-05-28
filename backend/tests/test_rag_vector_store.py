from pathlib import Path

import pytest

from app.core.exceptions import ToolError
from app.rag.schemas import CodeChunk
from app.rag.vector_store import VectorStore


def test_vector_store_adds_and_searches_chunks() -> None:
    store = VectorStore()
    chunks = [
        CodeChunk(file_path="agent.py", start_line=1, end_line=3, content="agent executor"),
        CodeChunk(file_path="docker.md", start_line=1, end_line=2, content="docker compose"),
    ]

    store.add(chunks, [[1.0, 0.0], [0.0, 1.0]])
    results = store.search([1.0, 0.0], top_k=1)

    assert store.size == 2
    assert results[0].file_path == "agent.py"
    assert results[0].score == pytest.approx(1.0)


def test_vector_store_save_and_load(tmp_path: Path) -> None:
    path = tmp_path / "index.json"
    store = VectorStore()
    store.add([CodeChunk(file_path="a.py", start_line=1, end_line=1, content="hello")], [[1.0, 0.0]])
    store.save(path)

    loaded = VectorStore.load(path)

    assert loaded.size == 1
    assert loaded.search([1.0, 0.0])[0].content == "hello"


def test_vector_store_rejects_mismatched_lengths() -> None:
    store = VectorStore()

    with pytest.raises(ToolError, match="length mismatch"):
        store.add([CodeChunk(file_path="a.py", start_line=1, end_line=1, content="x")], [])


def test_vector_store_rejects_dimension_mismatch() -> None:
    store = VectorStore()
    store.add([CodeChunk(file_path="a.py", start_line=1, end_line=1, content="x")], [[1.0, 0.0]])

    with pytest.raises(ToolError, match="dimensions"):
        store.search([1.0])
