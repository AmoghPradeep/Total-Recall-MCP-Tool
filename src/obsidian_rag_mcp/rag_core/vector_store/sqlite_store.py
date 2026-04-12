from __future__ import annotations

import json
import math
import sqlite3
from pathlib import Path

from obsidian_rag_mcp.models import Chunk, RetrievalResult
from obsidian_rag_mcp.rag_core.vector_store.base import VectorStore


class SQLiteVectorStore(VectorStore):
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS vectors (
                    chunk_id TEXT PRIMARY KEY,
                    doc_path TEXT NOT NULL,
                    content TEXT NOT NULL,
                    position INTEGER NOT NULL,
                    vector_json TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_vectors_doc_path ON vectors(doc_path)")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tags (
                    tag TEXT PRIMARY KEY,
                    usage_count INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS doc_tags (
                    doc_path TEXT NOT NULL,
                    tag TEXT NOT NULL,
                    PRIMARY KEY (doc_path, tag)
                )
                """
            )

    def upsert_chunks(self, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("chunks and vectors must have equal length")
        rows = [
            (chunk.chunk_id, chunk.doc_path, chunk.content, chunk.position, json.dumps(vector))
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]
        with self._connect() as conn:
            conn.executemany(
                """
                INSERT INTO vectors(chunk_id, doc_path, content, position, vector_json)
                VALUES(?,?,?,?,?)
                ON CONFLICT(chunk_id)
                DO UPDATE SET
                    doc_path=excluded.doc_path,
                    content=excluded.content,
                    position=excluded.position,
                    vector_json=excluded.vector_json
                """,
                rows,
            )

    def delete_by_doc(self, doc_path: str) -> int:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM vectors WHERE doc_path = ?", (doc_path,))
            return cur.rowcount

    def query(self, vector: list[float], k: int) -> list[RetrievalResult]:
        if k <= 0:
            return []
        with self._connect() as conn:
            rows = conn.execute("SELECT chunk_id, doc_path, content, vector_json FROM vectors").fetchall()

        scored: list[RetrievalResult] = []
        for row in rows:
            cand = json.loads(row["vector_json"])
            score = _cosine(vector, cand)
            scored.append(
                RetrievalResult(
                    chunk_id=row["chunk_id"],
                    doc_path=row["doc_path"],
                    content=row["content"],
                    score=score,
                )
            )
        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[:k]

    def get_tags(self) -> list[str]:
        with self._connect() as conn:
            rows = conn.execute("SELECT tag FROM tags ORDER BY usage_count DESC, tag ASC").fetchall()
        return [r["tag"] for r in rows]

    def upsert_doc_tags(self, doc_path: str, tags: list[str]) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM doc_tags WHERE doc_path = ?", (doc_path,))
            conn.executemany("INSERT OR IGNORE INTO tags(tag, usage_count) VALUES(?, 0)", [(t,) for t in tags])
            conn.executemany("UPDATE tags SET usage_count = usage_count + 1 WHERE tag = ?", [(t,) for t in tags])
            conn.executemany(
                "INSERT OR REPLACE INTO doc_tags(doc_path, tag) VALUES(?,?)",
                [(doc_path, t) for t in tags],
            )


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    length = min(len(a), len(b))
    a = a[:length]
    b = b[:length]
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)
