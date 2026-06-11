from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from app.rag.embeddings import LocalHashEmbeddingClient, create_embedding_client
from app.rag.index_cache import get_index_cache, project_key as make_project_key
from app.rag.retriever import CodeRetriever
from app.tools.base import BaseTool
from app.tools.file_tools import _resolve_existing_dir


class RetrieveCodeArgs(BaseModel):
    project_path: str
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    embedding_provider: str = "local"


class RetrieveCodeTool(BaseTool):
    name = "retrieve_code"
    description = "Retrieve Top-K semantically relevant code chunks with file paths and line ranges. Indexes the project on first call; subsequent calls within the TTL reuse the cached index."
    args_schema = RetrieveCodeArgs

    def run(self, **kwargs: Any) -> dict[str, Any]:
        args = self.validate_args(kwargs)
        assert isinstance(args, RetrieveCodeArgs)
        root = _resolve_existing_dir(args.project_path)
        pkey = make_project_key(str(root))
        cache = get_index_cache()

        embedding_client = (
            LocalHashEmbeddingClient()
            if args.embedding_provider == "local"
            else create_embedding_client(args.embedding_provider)
        )
        # Each project gets its own isolated Chroma collection via pkey,
        # so indexing project B never overwrites project A's index (fixes D7).
        retriever = CodeRetriever(
            embedding_client=embedding_client,
            collection_name=pkey,
        )

        if not cache.is_fresh(pkey):
            stats = retriever.index_project(root)
            cache.mark_indexed(pkey)
            indexed_files = stats["indexed_files"]
            chunks = stats["chunks"]
        else:
            # Cache hit: skip re-indexing entirely (fixes D5 performance disaster).
            indexed_files = -1
            chunks = -1

        results = retriever.search(args.query, top_k=args.top_k)
        return {
            "project_path": str(Path(root)),
            "query": args.query,
            "indexed_files": indexed_files,
            "chunks": chunks,
            "cache_hit": indexed_files == -1,
            "matches": [
                {
                    "file_path": chunk.file_path,
                    "start_line": chunk.start_line,
                    "end_line": chunk.end_line,
                    "content": chunk.content,
                    "score": chunk.score,
                }
                for chunk in results
            ],
        }
