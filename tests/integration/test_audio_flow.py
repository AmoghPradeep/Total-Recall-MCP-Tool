from pathlib import Path

from total_recall.background_worker.service import BackgroundWorker
from total_recall.config import AppConfig


def test_audio_ingestion_end_to_end(tmp_path: Path, monkeypatch) -> None:
    vault = tmp_path / "vault"
    incoming = tmp_path / "incoming"
    audio = incoming / "audio"
    pdf = incoming / "pdf"
    image = incoming / "image"
    text = incoming / "text"
    for p in (vault, audio, pdf, image, text):
        p.mkdir(parents=True, exist_ok=True)

    cfg = AppConfig(
        vault_path=vault,
        incoming_root=incoming,
        db_path=tmp_path / "db.sqlite3",
        queue_path=tmp_path / "jobs.jsonl",
        manifest_path=tmp_path / "manifest.json",
    )

    monkeypatch.setattr("total_recall.background_worker.watchers.is_stable_file", lambda *_args, **_kwargs: True)
    monkeypatch.setattr("total_recall.background_worker.audio_pipeline.compress_for_asr_tempdir", lambda path: path)

    (audio / "note.m4a").write_bytes(b"fake audio")
    worker = BackgroundWorker(cfg)
    worker.llm_client.transcribe_audio = lambda *_args, **_kwargs: "spoken transcript about learning systems"
    worker.llm_client.chat = lambda *_args, **_kwargs: (
        '{"fileName":"Learning Systems","relativePath":"Topics/Learning","content":"# Learning Systems\\n\\n## 1. Transcript\\nspoken transcript about learning systems\\n\\n## 2. Summary & Takeaways\\n- learning systems\\n\\n## 3. Tags\\n- learning\\n- systems","tags":["learning","systems"]}'
    )

    queued = worker.scan_once()
    assert queued["audio"] == 1
    metrics = worker.process_queue_once()
    assert metrics["processed"] == 1

    md = vault / "Topics" / "Learning" / "Learning Systems.md"
    assert md.exists()
    text = md.read_text(encoding="utf-8")
    assert not text.startswith("# ")
    assert "## Sources" in text
    assert "[[z.rawdata/audio/note_" in text
    assert "|Original Audio]]" in text
