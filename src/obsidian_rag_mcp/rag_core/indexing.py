from __future__ import annotations

from pathlib import Path

from obsidian_rag_mcp.rag_core.chunking import chunk_text
from obsidian_rag_mcp.rag_core.embeddings import EmbeddingService
from obsidian_rag_mcp.rag_core.vector_store.base import VectorStore


def index_markdown_document(
    doc_path: Path,
    content: str,
    embedding_service: EmbeddingService,
    vector_store: VectorStore,
    chunk_size: int,
    chunk_overlap: int,
) -> int:
    chunks = chunk_text(content, str(doc_path), chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    if not chunks:
        vector_store.delete_by_doc(str(doc_path))
        return 0
    vectors = embedding_service.embed_texts([c.content for c in chunks])
    vector_store.delete_by_doc(str(doc_path))
    vector_store.upsert_chunks(chunks, vectors)
    return len(chunks)
