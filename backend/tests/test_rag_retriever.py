from pathlib import Path

from app.rag.embeddings import LocalHashEmbeddingClient
from app.rag.retriever import CodeRetriever


def test_retriever_indexes_project_and_returns_relevant_chunk(tmp_path: Path) -> None:
    (tmp_path / "agent.py").write_text("class AgentExecutor:\n    pass\n", encoding="utf-8")
    (tmp_path / "deployment.md").write_text("docker compose up", encoding="utf-8")
    retriever = CodeRetriever(embedding_client=LocalHashEmbeddingClient(dimension=64))

    stats = retriever.index_project(tmp_path)
    results = retriever.search("AgentExecutor agent", top_k=1)

    assert stats["indexed_files"] == 2
    assert stats["chunks"] == 2
    assert results[0].file_path == "agent.py"
    assert results[0].start_line == 1
    assert "AgentExecutor" in results[0].content


def test_retriever_can_save_and_load_index(tmp_path: Path) -> None:
    (tmp_path / "registry.py").write_text("class ToolRegistry:\n    pass", encoding="utf-8")
    index_path = tmp_path / "vectors"
    client = LocalHashEmbeddingClient(dimension=64)
    retriever = CodeRetriever(embedding_client=client)

    retriever.index_project(tmp_path, save_path=index_path)
    loaded = CodeRetriever.from_saved_index(index_path, embedding_client=client)
    results = loaded.search("ToolRegistry", top_k=1)

    assert results[0].file_path == "registry.py"

