## Why

Knowledge in an Obsidian vault is growing from multiple sources (audio notes, scanned/handwritten PDFs, and direct markdown edits), but it is not consistently normalized or retrievable through MCP-native semantic search. Building a Python RAG-based MCP tool now enables always-on ingestion plus low-latency context retrieval for downstream assistants and workflows.

## What Changes

- Add a Windows-startup background ingestion service with filesystem watchers for audio and PDF drop folders.
- Add audio ingestion pipeline for new `.m4a` files: transcription, markdown normalization, vault write, chunking, embedding, and vector upsert.
- Add PDF ingestion pipeline for new `.pdf` files: OCR/text extraction via LLM normalization, summary generation, markdown write, chunking, embedding, and vector upsert.
- Add explicit local model lifecycle management to load/eject transformer and Ollama-compatible models per job.
- Add a foreground MCP indexing tool to detect changed/new markdown files in the Obsidian vault and regenerate embeddings for only the delta.
- Add an MCP retrieval tool that returns top-`k` relevant chunks from vector storage for a query.
- Add metadata + idempotency model to prevent duplicate processing and enable safe reprocessing when source files change.

## Capabilities

### New Capabilities
- `background-knowledge-generation`: Watch configured audio/PDF folders, normalize inputs into vault markdown, and index resulting content.
- `foreground-knowledge-generation`: Provide an MCP tool that computes markdown deltas in the vault and refreshes embeddings only for changed content.
- `mcp-context-retrieval`: Provide an MCP tool that returns top-`k` semantically relevant chunks with source metadata from the vector database.

### Modified Capabilities
- None.

## Impact

- Affected code: new Python packages/modules for watchers, ingestion pipelines, model orchestration, chunking/embedding, vector storage adapter, MCP server/tool handlers, and config management.
- APIs: MCP tool contracts for reindex and query flows; optional local HTTP calls for Ollama runtime.
- Dependencies/systems: transformer-based ASR model runtime, Ollama-compatible local LLM runtime, PDF/OCR processing library, vector DB (e.g., Chroma/FAISS/Qdrant), Windows Task Scheduler or Startup integration, structured logging/metrics.
- Operational impact: background process CPU/RAM spikes during model loads; requires queueing, backpressure, and retry handling.
