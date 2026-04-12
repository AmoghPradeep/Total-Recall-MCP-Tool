from pathlib import Path

from obsidian_rag_mcp.background_worker.service import BackgroundWorker
from obsidian_rag_mcp.config import AppConfig


def test_pdf_ingestion_end_to_end(tmp_path: Path, monkeypatch) -> None:
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
    monkeypatch.setattr(
        "obsidian_rag_mcp.background_worker.pdf_pipeline.convert_pdf_to_jpg_pages",
        lambda _pdf, image_dir: [image_dir / "page-1.jpg"],
    )

    (pdf / "handwritten.pdf").write_bytes(b"fake pdf")
    worker = BackgroundWorker(cfg)

    queued = worker.scan_once()
    assert queued["pdf"] == 1
    metrics = worker.process_queue_once()
    assert metrics["processed"] == 1

    md = vault / "handwritten.md"
    assert md.exists()
    text = md.read_text(encoding="utf-8")
    assert "# Summary" in text
    assert "# Content" in text
