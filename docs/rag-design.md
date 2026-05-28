# RAG Design

The RAG subsystem gives AICodePilot codebase semantic retrieval. The first version uses project scanning, line-based chunking, embeddings, a vector store, and Top-K retrieval.

## Flow

1. Scan project files with ignore rules.
2. Read text/code files safely.
3. Split content into chunks with file path and line metadata.
4. Generate embeddings.
5. Store vectors and metadata.
6. Embed query and retrieve Top-K chunks.
7. Inject relevant snippets into Agent context.
8. Return file paths, line numbers, snippets, and explanations.
