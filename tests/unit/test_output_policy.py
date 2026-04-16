from pathlib import Path

from total_recall.background_worker.output_policy import (
    build_aliased_vault_link,
    canonicalize_markdown_content,
    list_eligible_output_dirs,
    sanitize_relative_dir,
)


def test_sanitize_relative_dir_rejects_reserved_and_overdeep_paths() -> None:
    reserved_dir, reserved_fallback, reserved_reason = sanitize_relative_dir("z.rawdata/text")
    assert reserved_fallback is True
    assert reserved_dir.as_posix() == "inbox/imported"
    assert "reserved output root" in reserved_reason

    deep_dir, deep_fallback, deep_reason = sanitize_relative_dir("Topics/AI/RAG/Chunking")
    assert deep_fallback is True
    assert deep_dir.as_posix() == "inbox/imported"
    assert "max depth" in deep_reason


def test_list_eligible_output_dirs_excludes_reserved_and_limits_depth(tmp_path: Path) -> None:
    (tmp_path / "Topics" / "AI" / "RAG").mkdir(parents=True)
    (tmp_path / "z.rawdata" / "text").mkdir(parents=True)
    (tmp_path / "Topics" / "AI" / "RAG" / "TooDeep").mkdir(parents=True)

    dirs = list_eligible_output_dirs(tmp_path)

    assert "Topics" in dirs
    assert "Topics/AI" in dirs
    assert "Topics/AI/RAG" in dirs
    assert "z.rawdata/text" not in dirs
    assert "Topics/AI/RAG/TooDeep" not in dirs


def test_canonicalize_markdown_content_strips_title_and_replaces_sources(tmp_path: Path) -> None:
    raw_source = tmp_path / "z.rawdata" / "text" / "ideas.txt"
    raw_source.parent.mkdir(parents=True)
    raw_source.write_text("source", encoding="utf-8")
    source_link = build_aliased_vault_link(tmp_path, raw_source, "Original Text")

    content = (
        "# Ideas Note\n\n"
        "## 1. Transcript\nThoughts about retrieval\n\n"
        "## 4. Resources\n- [[z.rawdata/text/ideas.txt]]\n"
    )

    result = canonicalize_markdown_content(content, source_links=[source_link])

    assert not result.startswith("# ")
    assert "## 4. Resources" not in result
    assert "\n## Source\n" not in result
    assert result.count("## Sources") == 1
    assert "[[z.rawdata/text/ideas.txt|Original Text]]" in result
