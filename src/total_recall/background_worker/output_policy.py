from __future__ import annotations

import re
from pathlib import Path

FALLBACK_RELATIVE_DIR = Path("inbox") / "imported"
APPROVED_OUTPUT_ROOTS = ("People", "Projects", "Areas", "Topics", "References")
MAX_OUTPUT_DEPTH = 3
RESERVED_OUTPUT_ROOTS = {"z.rawdata", ".obsidian", ".trash"}

_APPROVED_ROOT_LOOKUP = {root.lower(): root for root in APPROVED_OUTPUT_ROOTS}
_RESERVED_ROOT_LOOKUP = {root.lower() for root in RESERVED_OUTPUT_ROOTS}
_PROVENANCE_SECTION_RE = re.compile(
    r"(?ms)^##(?:\s+\d+\.)?\s+(?:Resources|Source|Sources)\s*\n.*?(?=^## |\Z)"
)


def safe_filename(name: str) -> str:
    name = name.strip()
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "-", name)
    name = re.sub(r"\s+", " ", name)
    cleaned = name[:150].strip(" .")
    return cleaned or "Untitled Note"


def safe_segment(segment: str) -> str:
    segment = segment.strip()
    segment = re.sub(r'[<>:"\\|?*\x00-\x1f]', "-", segment)
    segment = re.sub(r"\s+", " ", segment)
    return segment.strip(" .")


def sanitize_relative_dir(raw_relative_path: object) -> tuple[Path, bool, str]:
    if not isinstance(raw_relative_path, str):
        return FALLBACK_RELATIVE_DIR, True, "relativePath missing or non-string"

    proposed = raw_relative_path.strip()
    if not proposed:
        return FALLBACK_RELATIVE_DIR, True, "relativePath empty"

    normalized = proposed.replace("\\", "/")
    lowered = normalized.lower()

    is_absolute_like = (
        bool(re.match(r"^[a-zA-Z]:", normalized))
        or normalized.startswith("/")
        or normalized.startswith("//")
        or normalized.startswith("\\\\")
        or bool(re.match(r"^[a-zA-Z]--", normalized))
        or lowered.startswith("c--users")
    )
    if is_absolute_like:
        return FALLBACK_RELATIVE_DIR, True, f"absolute or malformed path: {proposed}"

    parts: list[str] = []
    for raw_part in normalized.split("/"):
        part = raw_part.strip()
        if not part or part == ".":
            continue
        if part == "..":
            return FALLBACK_RELATIVE_DIR, True, f"path traversal segment in: {proposed}"
        safe = safe_segment(part)
        if safe:
            parts.append(safe)

    if not parts:
        return FALLBACK_RELATIVE_DIR, True, "relativePath sanitized to empty"
    if len(parts) > MAX_OUTPUT_DEPTH:
        return FALLBACK_RELATIVE_DIR, True, f"path exceeds max depth {MAX_OUTPUT_DEPTH}: {proposed}"

    root_key = parts[0].lower()
    if root_key in _RESERVED_ROOT_LOOKUP:
        return FALLBACK_RELATIVE_DIR, True, f"reserved output root: {parts[0]}"
    if root_key not in _APPROVED_ROOT_LOOKUP:
        return FALLBACK_RELATIVE_DIR, True, f"unapproved output root: {parts[0]}"

    canonical_root = _APPROVED_ROOT_LOOKUP[root_key]
    return Path(canonical_root, *parts[1:]), False, ""


def list_eligible_output_dirs(vault_root: Path) -> list[str]:
    entries = {root for root in APPROVED_OUTPUT_ROOTS}
    for path in vault_root.rglob("*"):
        if not path.is_dir():
            continue
        rel = path.relative_to(vault_root).as_posix()
        parts = [part for part in rel.split("/") if part]
        if not parts or len(parts) > MAX_OUTPUT_DEPTH:
            continue
        root_key = parts[0].lower()
        if root_key in _RESERVED_ROOT_LOOKUP or root_key not in _APPROVED_ROOT_LOOKUP:
            continue
        parts[0] = _APPROVED_ROOT_LOOKUP[root_key]
        entries.add("/".join(parts))
    return sorted(entries, key=lambda value: (value.count("/"), value.lower()))


def build_directory_hint(vault_root: Path) -> str:
    return ",".join(list_eligible_output_dirs(vault_root))


def build_aliased_vault_link(vault_root: Path, source_path: Path, label: str) -> str:
    rel = source_path.resolve().relative_to(vault_root.resolve())
    clean_label = label.strip().replace("|", "-") or rel.stem
    return f"[[{rel.as_posix()}|{clean_label}]]"


def canonicalize_markdown_content(content: str, source_links: list[str] | None = None) -> str:
    normalized = str(content).replace("\r\n", "\n").strip()
    normalized = re.sub(r"\A# [^\n]+\n*", "", normalized, count=1)
    normalized = _PROVENANCE_SECTION_RE.sub("", normalized).strip()
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)

    unique_links = list(dict.fromkeys(link for link in (source_links or []) if link))
    if unique_links:
        source_body = unique_links[0] if len(unique_links) == 1 else "\n".join(f"- {link}" for link in unique_links)
        normalized = normalized.rstrip()
        if normalized:
            normalized += "\n\n"
        normalized += f"## Sources\n{source_body}"

    return normalized.rstrip() + "\n"
