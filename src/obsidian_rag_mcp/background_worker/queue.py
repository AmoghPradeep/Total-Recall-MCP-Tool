from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from threading import Lock


@dataclass(slots=True)
class IngestionJob:
    job_type: str
    source_path: str
    idempotency_key: str


class DurableJobQueue:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._seen_keys: set[str] = set()
        self._load_seen_keys()

    def _load_seen_keys(self) -> None:
        if not self.path.exists():
            return
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            self._seen_keys.add(row["idempotency_key"])

    def enqueue(self, job: IngestionJob) -> bool:
        with self._lock:
            if job.idempotency_key in self._seen_keys:
                return False
            self._seen_keys.add(job.idempotency_key)
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(job)) + "\n")
        return True

    def pop_all(self) -> list[IngestionJob]:
        with self._lock:
            if not self.path.exists():
                return []
            jobs: list[IngestionJob] = []
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                data = json.loads(line)
                jobs.append(IngestionJob(**data))
            self.path.write_text("", encoding="utf-8")
            return jobs
