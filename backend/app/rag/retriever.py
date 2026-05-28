import re
from pathlib import Path

from app.core.config import Settings, get_settings
from app.rag.chunker import CodeChunker
from app.rag.embeddings import BaseEmbeddingClient, create_embedding_client
from app.rag.indexer import ProjectIndexer
from app.rag.schemas import RetrievedChunk
from app.rag.vector_store import VectorStore

_QUERY_TOKEN_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|[\u4e00-\u9fff]+")
_TEST_OR_DOC_MARKERS = ("/tests/", "tests/", "docs/", "README.md")


class CodeRetriever:
    """Coordinate project indexing and Top-K code retrieval.

    The retriever is deliberately composed from small parts instead of hiding
    everything behind a framework. This keeps the RAG data flow inspectable:
    scan files, chunk text, embed chunks, add vectors, embed query, search.

    Local hash embeddings are useful for offline validation but are lexical and
    can over-rank docs/tests. The search method therefore applies a small hybrid
    rerank that rewards direct query-token hits and production source files.
    API embeddings still provide the main semantic score when configured.
    """

    def __init__(
        self,
        indexer: ProjectIndexer | None = None,
        chunker: CodeChunker | None = None,
        embedding_client: BaseEmbeddingClient | None = None,
        vector_store: VectorStore | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.indexer = indexer or ProjectIndexer()
        self.chunker = chunker or CodeChunker()
        self.embedding_client = embedding_client or create_embedding_client(settings=self.settings)
        self.vector_store = vector_store or VectorStore()

    def index_project(self, project_path: str | Path, save_path: str | Path | None = None) -> dict[str, int]:
        files = self.indexer.scan_files(project_path)
        chunks = self.chunker.chunk_project_files(files)
        embeddings = self.embedding_client.embed_texts([chunk.content for chunk in chunks]) if chunks else []
        self.vector_store.clear()
        self.vector_store.add(chunks, embeddings)

        if save_path is not None:
            self.vector_store.save(save_path)

        return {"indexed_files": len(files), "chunks": len(chunks)}

    def search(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        query_embedding = self.embedding_client.embed_query(query)
        candidate_count = max(top_k * 20, 50)
        candidates = self.vector_store.search(query_embedding, top_k=candidate_count)
        return self._rerank(query, candidates)[:top_k]

    def index_and_search(self, project_path: str | Path, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        self.index_project(project_path)
        return self.search(query, top_k=top_k)

    @classmethod
    def from_saved_index(
        cls,
        index_path: str | Path,
        embedding_client: BaseEmbeddingClient | None = None,
        settings: Settings | None = None,
    ) -> "CodeRetriever":
        resolved_settings = settings or get_settings()
        return cls(
            embedding_client=embedding_client or create_embedding_client(settings=resolved_settings),
            vector_store=VectorStore.load(index_path),
            settings=resolved_settings,
        )

    def _rerank(self, query: str, candidates: list[RetrievedChunk]) -> list[RetrievedChunk]:
        tokens = [token.lower() for token in _QUERY_TOKEN_PATTERN.findall(query)]
        if not tokens:
            return candidates

        reranked: list[RetrievedChunk] = []
        for chunk in candidates:
            searchable = f"{chunk.file_path}\n{chunk.content}".lower()
            file_path_text = chunk.file_path.lower()
            token_hits = sum(1 for token in tokens if token in searchable)
            file_token_hits = sum(1 for token in tokens if token in file_path_text)
            exact_query_bonus = 0.2 if query.lower() in searchable else 0.0
            source_bonus = self._source_file_bonus(chunk.file_path)
            intent_bonus = self._intent_file_bonus(tokens, chunk.file_path)
            hybrid_score = chunk.score + (0.08 * token_hits) + (0.16 * file_token_hits) + exact_query_bonus + source_bonus + intent_bonus
            reranked.append(
                RetrievedChunk(
                    file_path=chunk.file_path,
                    start_line=chunk.start_line,
                    end_line=chunk.end_line,
                    content=chunk.content,
                    score=hybrid_score,
                )
            )
        return sorted(reranked, key=lambda chunk: chunk.score, reverse=True)

    def _intent_file_bonus(self, tokens: list[str], file_path: str) -> float:
        normalized = file_path.replace("\\", "/").lower()
        token_set = set(tokens)
        if {"config", "settings", "env", "environment"} & token_set and normalized.endswith("backend/app/core/config.py"):
            return 0.25
        if {"registry", "toolregistry"} & token_set and normalized.endswith("backend/app/tools/registry.py"):
            return 0.2
        if {"agentexecutor", "executor"} & token_set and normalized.endswith("backend/app/agent/executor.py"):
            return 0.2
        return 0.0

    def _source_file_bonus(self, file_path: str) -> float:
        normalized = file_path.replace("\\", "/")
        if any(marker in normalized for marker in _TEST_OR_DOC_MARKERS):
            return -0.12
        if normalized.startswith("backend/app/") or normalized.startswith("frontend/"):
            return 0.12
        if normalized.endswith("requirements.txt") or normalized.endswith(".md"):
            return -0.08
        return 0.0



