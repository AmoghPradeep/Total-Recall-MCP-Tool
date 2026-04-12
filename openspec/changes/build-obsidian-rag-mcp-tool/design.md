## Context

This change introduces a Python-based Retrieval-Augmented Generation (RAG) pipeline around an Obsidian vault with two ingestion paths and one retrieval path. The current state has no standardized ingestion/indexing lifecycle for audio/PDF sources, no delta indexing for vault markdown changes, and no MCP-native query interface over embedded knowledge. Constraints include Windows-first operation for background startup, local/offline-friendly model execution (transformer ASR and Ollama-compatible LLM), and bounded memory usage while loading large models. Initial model choices are: ASR `cohere-transcribe-03-2026`, generation LLM `gemma4-26B-A4B` (`Q3_K_M` quantized), and embeddings `Qwen3-Embedding-0.6B`.

## Goals / Non-Goals

**Goals:**
- Provide a startup background service that watches audio/PDF folders and converts new files into normalized vault markdown.
- Ensure generated markdown is chunked, embedded, and upserted into a vector database with source metadata.
- Provide an MCP tool to reindex changed/new markdown deltas in the vault.
- Provide an MCP tool to query top-k relevant context chunks from vector DB.
- Enforce predictable model lifecycle (load on job start, eject on completion/failure) to control RAM use.

**Non-Goals:**
- Building cloud-hosted orchestration, multi-tenant auth, or remote managed vector services.
- Replacing Obsidian authoring workflows or providing a full UI.
- Achieving perfect OCR/transcription fidelity for every noisy or low-quality source.

## Decisions

1. Python modular architecture with three runtime modules: `background_worker`, `mcp_server`, and shared `rag_core`.
- Rationale: keeps long-running watchers separated from request/response MCP tool execution while sharing chunking, embedding, and vector logic.
- Alternative considered: single monolithic process handling watchers and MCP endpoints. Rejected due to tighter failure coupling and harder restart behavior.

2. Event-driven ingestion with durable job queue and idempotency keys.
- Rationale: file watchers can emit duplicate events; queue + idempotency (`source_path + mtime + size + checksum`) prevents duplicate indexing.
- Alternative considered: direct inline processing from watcher callbacks. Rejected because it risks missed events and blocked watcher threads.

3. Model runtime policy with localhost service detection and fallback load/eject.
- Rationale: generation should prefer reusing an already-running OpenAI-compatible service on `http://localhost:1234`; if unavailable, pipeline loads the local LLM, serves/invokes it, and ejects model after completion.
- Alternative considered: always load/eject model regardless of service state. Rejected due to unnecessary startup latency when a local service is already active.

4. Markdown normalization contract with domain tag governance.
- Rationale: all ingestion flows emit frontmatter + normalized sections (`source`, `created_at`, `summary`, `content`, `tags`) so chunking and retrieval stay consistent while enabling reusable domain taxonomy.
- Alternative considered: source-specific chunkers without normalization. Rejected because retrieval quality and metadata semantics become inconsistent.

5. Vector-store abstraction with local-first default.
- Rationale: define `VectorStore` interface (`upsert_chunks`, `delete_by_doc`, `query`) with Chroma as default adapter; enables future switch to FAISS/Qdrant.
- Alternative considered: hard-coding one backend. Rejected to reduce lock-in and testing limitations.

6. Foreground delta reindex via content-hash manifest.
- Rationale: maintain manifest keyed by markdown path to hash/version; changed/new files get re-embedded and removed files purge vectors.
- Alternative considered: full vault reindex on each invocation. Rejected for cost/latency.

7. PDF multimodal map-reduce conversion strategy.
- Rationale: convert PDF pages to images (`pdf -> jpg`), run page-level multimodal extraction/summarization, and combine with map-reduce to improve handwritten-content capture and long-document summarization.
- Alternative considered: single-pass OCR-only extraction. Rejected due to weaker handwritten capture and lower summary quality on mixed-layout documents.

8. MCP API shape for retrieval and indexing.
- Rationale: expose `reindex_vault_delta` and `query_vault_context` tools with strict input schema (`k`, query text); outputs include chunk text, score, and source metadata.
- Alternative considered: single overloaded MCP tool. Rejected for poorer ergonomics and weaker observability.

9. Configurable chunking with practical defaults.
- Rationale: keep chunk parameters runtime-configurable and start with recommended defaults (`chunk_size=800`, `chunk_overlap=120`, token-based) to balance retrieval precision and context continuity.
- Alternative considered: fixed chunking constants. Rejected because different vault note styles need tuning.

10. Tag catalog reuse with controlled novelty.
- Rationale: maintain a tag catalog in storage; generation prompts bias toward existing domain tags and allow a new tag only when no existing tag fits.
- Alternative considered: unconstrained per-document tag generation. Rejected due to taxonomy drift and inconsistent retrieval grouping.

## Risks / Trade-offs

- [High CPU/RAM spikes during model load] -> Mitigation: single-flight job execution per model type, queue backpressure, configurable concurrency limit.
- [File watcher race conditions/partial file writes] -> Mitigation: stable-file check (size/mtime unchanged across interval) before enqueue.
- [OCR/LLM normalization quality variance on handwritten PDFs] -> Mitigation: page-image multimodal extraction with map-reduce summary, store raw extraction alongside normalized markdown, annotate confidence flags.
- [Vector drift when source markdown is edited manually] -> Mitigation: foreground delta tool updates vectors by hash and removes stale chunk IDs.
- [Long-running process reliability on Windows startup] -> Mitigation: Task Scheduler wrapper, heartbeat logging, retry policy, and crash-safe manifest persistence.
- [Tag explosion and inconsistent domain labels] -> Mitigation: tag catalog reuse policy, similarity checks against existing tags, and explicit threshold for new-tag creation.

## Migration Plan

1. Introduce config file/env contract for vault paths, watched folders, model identifiers, chunk defaults, and vector backend.
2. Implement core pipeline modules and local integration tests.
3. Deploy background worker as startup task on Windows test machine.
4. Backfill existing vault markdown via one-time reindex command.
5. Enable MCP server tools for client integration and validate retrieval quality.
6. Rollback strategy: disable startup task and MCP tools, retain generated markdown; vector DB can be rebuilt from markdown manifest.

## Open Questions

- None for v1 scope; model/runtime and retrieval constraints are now fixed by current decisions.
