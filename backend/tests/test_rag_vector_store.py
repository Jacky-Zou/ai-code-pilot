from pathlib import Path

import pytest

from app.core.exceptions import ToolError
from app.rag.schemas import CodeChunk
from app.rag.vector_store import ChromaVectorStore, JsonVectorStore, create_vector_store


def test_json_vector_store_adds_and_searches_chunks() -> None:
    store = JsonVectorStore()
    chunks = [
        CodeChunk(file_path="agent.py", start_line=1, end_line=3, content="agent executor"),
        CodeChunk(file_path="docker.md", start_line=1, end_line=2, content="docker compose"),
    ]

    store.add(chunks, [[1.0, 0.0], [0.0, 1.0]])
    results = store.search([1.0, 0.0], top_k=1)

    assert store.size == 2
    assert results[0].file_path == "agent.py"
    assert results[0].score == pytest.approx(1.0)


def test_json_vector_store_save_and_load(tmp_path: Path) -> None:
    path = tmp_path / "index.json"
    store = JsonVectorStore()
    store.add([CodeChunk(file_path="a.py", start_line=1, end_line=1, content="hello")], [[1.0, 0.0]])
    store.save(path)

    loaded = JsonVectorStore.load(path)

    assert loaded.size == 1
    assert loaded.search([1.0, 0.0])[0].content == "hello"


def test_chroma_vector_store_adds_searches_and_persists(tmp_path: Path) -> None:
    store = ChromaVectorStore(persist_directory=tmp_path / "chroma", collection_name="test_code")
    chunks = [
        CodeChunk(file_path="registry.py", start_line=1, end_line=2, content="class ToolRegistry"),
        CodeChunk(file_path="deploy.md", start_line=1, end_line=1, content="docker compose"),
    ]

    store.clear()
    store.add(chunks, [[1.0, 0.0], [0.0, 1.0]])
    results = store.search([1.0, 0.0], top_k=1)
    reloaded = ChromaVectorStore.load(tmp_path / "chroma", collection_name="test_code")

    assert store.size == 2
    assert results[0].file_path == "registry.py"
    assert reloaded.search([1.0, 0.0], top_k=1)[0].file_path == "registry.py"


def test_create_vector_store_defaults_to_chroma(tmp_path: Path) -> None:
    store = create_vector_store(persist_directory=tmp_path / "chroma", collection_name="factory_code")

    assert isinstance(store, ChromaVectorStore)


def test_vector_store_rejects_mismatched_lengths() -> None:
    store = JsonVectorStore()

    with pytest.raises(ToolError, match="length mismatch"):
        store.add([CodeChunk(file_path="a.py", start_line=1, end_line=1, content="x")], [])


def test_vector_store_rejects_dimension_mismatch() -> None:
    store = JsonVectorStore()
    store.add([CodeChunk(file_path="a.py", start_line=1, end_line=1, content="x")], [[1.0, 0.0]])

    with pytest.raises(ToolError, match="dimensions"):
        store.search([1.0])
