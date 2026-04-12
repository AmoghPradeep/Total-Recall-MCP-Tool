from __future__ import annotations

import hashlib
import time
from pathlib import Path

from obsidian_rag_mcp.background_worker.queue import DurableJobQueue, IngestionJob


def compute_idempotency_key(path: Path) -> str:
    st = path.stat()
    raw = f"{path.resolve()}|{st.st_mtime_ns}|{st.st_size}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def is_stable_file(path: Path, wait_seconds: float = 1.5) -> bool:
    first = path.stat()
    time.sleep(wait_seconds)
    second = path.stat()
    return first.st_size == second.st_size and first.st_mtime_ns == second.st_mtime_ns


def scan_and_enqueue(audio_dir: Path, pdf_dir: Path, queue: DurableJobQueue) -> dict[str, int]:
    counts = {"audio": 0, "pdf": 0}
    for ext, folder, kind in (("*.m4a", audio_dir, "audio"), ("*.pdf", pdf_dir, "pdf")):
        for file in folder.glob(ext):
            if not is_stable_file(file):
                continue
            job = IngestionJob(job_type=kind, source_path=str(file), idempotency_key=compute_idempotency_key(file))
            if queue.enqueue(job):
                counts[kind] += 1
    return counts
