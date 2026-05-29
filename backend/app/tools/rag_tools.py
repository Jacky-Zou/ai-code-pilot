from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from app.rag.embeddings import LocalHashEmbeddingClient, create_embedding_client
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
    description = "Index a project and retrieve Top-K semantically relevant code chunks with file paths and line ranges."
    args_schema = RetrieveCodeArgs

    def run(self, **kwargs: Any) -> dict[str, Any]:
        args = self.validate_args(kwargs)
        assert isinstance(args, RetrieveCodeArgs)
        root = _resolve_existing_dir(args.project_path)

        # The local provider keeps the CLI and tests usable without external API
        # credentials. Production requests can pass embedding_provider="openai"
        # to use the configured OpenAI embedding model.
        embedding_client = (
            LocalHashEmbeddingClient() if args.embedding_provider == "local" else create_embedding_client(args.embedding_provider)
        )
        retriever = CodeRetriever(embedding_client=embedding_client)
        stats = retriever.index_project(root)
        chunks = retriever.search(args.query, top_k=args.top_k)

        return {
            "project_path": str(Path(root)),
            "query": args.query,
            "indexed_files": stats["indexed_files"],
            "chunks": stats["chunks"],
            "matches": [
                {
                    "file_path": chunk.file_path,
                    "start_line": chunk.start_line,
                    "end_line": chunk.end_line,
                    "content": chunk.content,
                    "score": chunk.score,
                }
                for chunk in chunks
            ],
        }
