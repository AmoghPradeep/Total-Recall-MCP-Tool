## 1. Project Skeleton and Configuration

- [x] 1.1 Create Python package structure for `background_worker`, `mcp_server`, and shared `rag_core` modules
- [x] 1.2 Add runtime dependencies for file watching, MCP server SDK, embeddings, vector store adapter, and PDF/audio processing
- [x] 1.3 Implement typed configuration loader for vault path, watched folders, model IDs, chunking settings, and vector backend
- [x] 1.4 Add structured logging and common error/result types used across ingestion and MCP tools
- [x] 1.5 Set default model config values: `cohere-transcribe-03-2026`, `gemma4-26B-A4B` (`Q3_K_M`), and `Qwen3-Embedding-0.6B`

## 2. Core RAG Indexing Components

- [x] 2.1 Implement markdown normalizer contract (frontmatter + canonical sections) for generated and vault markdown
- [x] 2.2 Implement chunking pipeline with configurable chunk size/overlap and stable chunk IDs
- [x] 2.3 Implement embedding service wrapper with retry/backoff and batch support
- [x] 2.4 Implement `VectorStore` interface and initial local backend adapter (including upsert, delete-by-doc, and query)

## 3. Background Knowledge Generation (Audio/PDF)

- [x] 3.1 Implement Windows-compatible folder watchers with stable-file detection and enqueue semantics
- [x] 3.2 Implement durable ingestion queue and idempotency key generation for source file versions
- [x] 3.3 Implement model lifecycle manager with `http://localhost:1234` health check, API-first reuse, and fallback local load/eject behavior
- [x] 3.4 Implement audio pipeline: `.m4a` transcription -> markdown normalization -> vault write
- [x] 3.5 Implement PDF pipeline: `pdf -> jpg` conversion, page-level multimodal extraction, map-reduce summary generation, and vault write
- [x] 3.6 Chain post-generation indexing for both pipelines (chunk, embed, vector upsert) with provenance metadata
- [x] 3.7 Implement domain-tag generation with catalog reuse policy, new-tag gating, and DB persistence of tag assignments
- [x] 3.8 Add failure handling, retries, and guaranteed model ejection in all error paths

## 4. Foreground Knowledge Generation MCP Tool

- [x] 4.1 Define MCP tool contract for `reindex_vault_delta` with validation and result schema
- [x] 4.2 Implement vault markdown scanner and fingerprint manifest persistence/load on startup
- [x] 4.3 Implement delta planner for new/changed/deleted markdown files
- [x] 4.4 Implement delta execution to re-embed changed/new files and delete vectors for removed files
- [x] 4.5 Return deterministic summary metrics (processed, skipped, deleted, errors) from tool responses

## 5. MCP Context Retrieval Tool

- [x] 5.1 Define MCP tool contract for `query_vault_context` with query text and `k` (no metadata filters in v1)
- [x] 5.2 Implement retrieval service that validates/clamps `k` and executes vector similarity search
- [x] 5.3 Format response payload with ranked chunks, scores, source file path, and chunk identifiers

## 6. Startup, Packaging, and Validation

- [x] 6.1 Add Windows startup integration script (Task Scheduler registration) for background worker
- [x] 6.2 Add CLI entrypoints for background worker and MCP server processes
- [x] 6.3 Add unit tests for chunking, idempotency, manifest delta detection, and retrieval validation rules
- [x] 6.4 Add integration tests for end-to-end audio/PDF ingestion and MCP reindex/query flows with local fixtures
- [x] 6.5 Document runbook for configuration, startup setup, and recovery/rebuild steps
