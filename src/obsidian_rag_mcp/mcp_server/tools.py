from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from obsidian_rag_mcp.config import AppConfig
from obsidian_rag_mcp.rag_core.embeddings import EmbeddingService
from obsidian_rag_mcp.rag_core.indexing import index_markdown_document
from obsidian_rag_mcp.rag_core.manifest import VaultManifest, compute_vault_fingerprints
from obsidian_rag_mcp.rag_core.retrieval import RetrievalService
from obsidian_rag_mcp.rag_core.vector_store.sqlite_store import SQLiteVectorStore


@dataclass(slots=True)
class ReindexResult:
    processed: int
    skipped: int
    deleted: int
    errors: int


class MCPTools:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.store = SQLiteVectorStore(config.db_path)
        self.embeddings = EmbeddingService(config.models.llm_service_url, config.models.embedding_model)
        self.manifest = VaultManifest(config.manifest_path)
        self.retrieval = RetrievalService(self.embeddings, self.store)

    def reindex_vault_delta(self) -> dict:
        previous = self.manifest.load()
        current = compute_vault_fingerprints(self.config.vault_path)

        prev_paths = set(previous)
        curr_paths = set(current)

        deleted = prev_paths - curr_paths
        new_or_changed = {p for p in curr_paths if previous.get(p) != current[p]}

        metrics = ReindexResult(processed=0, skipped=0, deleted=0, errors=0)

        for path in sorted(deleted):
            self.store.delete_by_doc(path)
            metrics.deleted += 1

        for path in sorted(new_or_changed):
            try:
                md_path = Path(path)
                content = md_path.read_text(encoding="utf-8")
                count = index_markdown_document(
                    md_path,
                    content,
                    self.embeddings,
                    self.store,
                    chunk_size=self.config.chunking.chunk_size,
                    chunk_overlap=self.config.chunking.chunk_overlap,
                )
                if count > 0:
                    metrics.processed += 1
                else:
                    metrics.skipped += 1
            except Exception:
                metrics.errors += 1

        for path in sorted(curr_paths - new_or_changed):
            metrics.skipped += 1

        self.manifest.save(current)
        return metrics.__dict__

    def query_vault_context(self, query: str, k: int = 5) -> dict:
        results = self.retrieval.query(query, k)
        return {"k": len(results), "results": results}
