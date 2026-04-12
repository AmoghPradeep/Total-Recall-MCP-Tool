from __future__ import annotations

from abc import ABC, abstractmethod

from obsidian_rag_mcp.models import Chunk, RetrievalResult


class VectorStore(ABC):
    @abstractmethod
    def upsert_chunks(self, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete_by_doc(self, doc_path: str) -> int:
        raise NotImplementedError

    @abstractmethod
    def query(self, vector: list[float], k: int) -> list[RetrievalResult]:
        raise NotImplementedError
