# RAG Design

The RAG subsystem gives AICodePilot codebase retrieval that can cite files, line ranges, snippets, and similarity scores. Phase 2 implements the complete local retrieval loop and keeps each part small enough to test independently.

## Implemented Flow

1. Scan the project with `ProjectIndexer`.
2. Skip dependency, build, cache, VCS, oversized, unsupported, and binary files.
3. Split files into line-based `CodeChunk` objects with `file_path`, `start_line`, `end_line`, and `content`.
4. Generate embeddings through a provider interface.
5. Add vectors and chunk metadata to `VectorStore`.
6. Embed the user query.
7. Search Top-K chunks by cosine similarity.
8. Return file paths, line numbers, snippets, scores, and explanations through the Agent.

## Scanner

`backend/app/rag/indexer.py` scans text and code files only. It ignores common unsafe or noisy directories such as `.git`, `node_modules`, `.venv`, `dist`, `build`, `.next`, `tests`, caches, and temporary folders. It reads only a small byte sample to reject binary files and skips files above the configured size limit.

## Chunker

`backend/app/rag/chunker.py` uses deterministic line windows. This is simple but interview-friendly: every retrieved chunk can be traced back to exact source lines. The implementation supports overlap and can later be extended to tree-sitter or AST-based function/class chunking.

## Embeddings

`backend/app/rag/embeddings.py` provides:

- `OpenAIEmbeddingClient`: default production embedding provider using `EMBEDDING_MODEL`.
- `LocalHashEmbeddingClient`: deterministic local embedding for unit tests and offline demos.

The OpenAI client raises a clear configuration error when `OPENAI_API_KEY` is missing. The local provider keeps the development workflow verifiable without network access.

## Vector Store

`backend/app/rag/vector_store.py` implements a Chroma-backed vector store as the default Phase 2 backend. `ChromaVectorStore` stores supplied embeddings, source documents, and metadata under `VECTOR_STORE_PATH`, then returns Top-K chunks with file path, line range, content, and similarity score. A lightweight `JsonVectorStore` remains available for deterministic unit tests and fallback debugging, but runtime retrieval defaults to Chroma through `VECTOR_STORE_BACKEND=chroma`.

## Retriever

`backend/app/rag/retriever.py` composes the scanner, chunker, embedding client, and vector store. It supports indexing a project, saving/loading an index, and querying Top-K relevant code chunks. For offline local embeddings, it applies a lightweight hybrid rerank that combines vector score, query-token hits, source-file priority, and path intent bonuses so implementation files rank ahead of tests or docs for code-location questions.

## Agent Tool

`retrieve_code(project_path, query, top_k)` is registered in the Tool Registry. The Agent can call it when the user asks where logic is implemented or needs semantic code context. The tool returns references shaped for UI/API responses:

```json
{
  "file_path": "backend/app/agent/executor.py",
  "start_line": 1,
  "end_line": 80,
  "content": "...",
  "score": 0.82
}
```


