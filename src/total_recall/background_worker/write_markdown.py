import json
import logging
import re
from pathlib import Path

from total_recall.background_worker.output_policy import (
    FALLBACK_RELATIVE_DIR,
    canonicalize_markdown_content,
    safe_filename,
    sanitize_relative_dir,
)

LOG = logging.getLogger(__name__)


def resolve_safe_output_dir(vault_root: Path, raw_relative_path: object) -> tuple[Path, bool]:
    relative_dir, used_fallback, reason = sanitize_relative_dir(raw_relative_path)
    vault_root_resolved = vault_root.resolve()
    candidate = (vault_root_resolved / relative_dir).resolve()

    try:
        candidate.relative_to(vault_root_resolved)
    except ValueError:
        used_fallback = True
        reason = reason or f"out-of-vault path after resolve: {candidate}"
        candidate = (vault_root_resolved / FALLBACK_RELATIVE_DIR).resolve()

    if used_fallback:
        LOG.warning("Using fallback markdown destination due to invalid relativePath: %s", reason)

    candidate.mkdir(parents=True, exist_ok=True)
    return candidate, used_fallback


def process_json_response(
    json_parameters: str,
    obsidian_vault_path: Path,
    source_links: list[str] | None = None,
) -> tuple[Path, list[str]]:
    """
    Parses LLM JSON output and creates a markdown file in the given Obsidian vault.

    Args:
        json_parameters (str): JSON string from LLM containing `fileName` and `content`
        obsidian_vault_path (str): Path to your Obsidian vault directory

    Returns:
        Path: Full path of the created markdown file
    """

    LOG.debug("Processing markdown JSON response vault_path=%s", obsidian_vault_path)

    # Clean possible markdown fences
    cleaned = json_parameters.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    # Parse JSON
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        LOG.error("Failed to decode markdown JSON response vault_path=%s", obsidian_vault_path)
        raise ValueError(f"Invalid JSON input: {e}")

    # Extract fields
    file_name = safe_filename(str(data.get("fileName", "Untitled Note")))
    output_dir, _ = resolve_safe_output_dir(obsidian_vault_path, data.get("relativePath", ""))

    raw_content = str(data.get("content", ""))
    content = canonicalize_markdown_content(raw_content, source_links=source_links)
    tags = data.get("tags", [])

    if not isinstance(tags, list):
        LOG.error("Invalid tags payload type=%s vault_path=%s", type(tags).__name__, obsidian_vault_path)
        raise ValueError("Tags must be a list")

    tags = [str(tag).strip() for tag in tags if str(tag).strip()]

    if not content.strip():
        LOG.error("Refusing to create markdown file with empty content vault_path=%s file_name=%s", obsidian_vault_path, file_name)
        raise ValueError("Content is empty. Cannot create markdown file.")

    # Create file path
    file_path = output_dir / f"{file_name}.md"

    # Avoid overwriting existing files
    counter = 1
    while file_path.exists():
        LOG.debug("Markdown target already exists, incrementing suffix path=%s", file_path)
        file_path = output_dir / f"{file_name} {counter}.md"
        counter += 1

    # Write file
    file_path.write_text(content, encoding="utf-8")
    LOG.info("Wrote markdown note path=%s tag_count=%s", file_path, len(tags))

    return file_path, tags
