from pathlib import Path

from obsidian_rag_mcp.background_worker.service import BackgroundWorker
from obsidian_rag_mcp.config import AppConfig
from obsidian_rag_mcp.rag_core.chunking import chunk_text


def test_audio_ingestion_end_to_end(tmp_path: Path, monkeypatch) -> None:
    vault = tmp_path / "vault"
    audio = tmp_path / "audio"
    pdf = tmp_path / "pdf"
    for p in (vault, audio, pdf):
        p.mkdir(parents=True, exist_ok=True)

    cfg = AppConfig(
        vault_path=vault,
        audio_watch_path=audio,
        pdf_watch_path=pdf,
        db_path=tmp_path / "db.sqlite3",
        queue_path=tmp_path / "jobs.jsonl",
        manifest_path=tmp_path / "manifest.json",
    )

    monkeypatch.setattr("obsidian_rag_mcp.background_worker.watchers.is_stable_file", lambda *_args, **_kwargs: True)

    (audio / "note.m4a").write_bytes(b"fake audio")
    worker = BackgroundWorker(cfg)

    queued = worker.scan_once()
    assert queued["audio"] == 1
    metrics = worker.process_queue_once()
    assert metrics["processed"] == 1

    md = vault / "note.md"
    assert md.exists()
    text = md.read_text(encoding="utf-8")
    assert "# Summary" in text
    assert "tags:" in text
