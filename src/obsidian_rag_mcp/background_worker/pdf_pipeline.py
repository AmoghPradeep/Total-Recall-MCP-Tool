from __future__ import annotations

import logging
import shutil
import tempfile
from pathlib import Path
from uuid import uuid4
from PIL import Image

try:
    import pypdfium2 as pdfium
except Exception:  # pragma: no cover
    pdfium = None

from obsidian_rag_mcp.background_worker.system_prompts import (
    get_pdf_note_json_prompt,
    get_pdf_page_extract_prompt,
    get_pdf_reduce_prompt,
    get_pdf_tags_prompt,
)
from obsidian_rag_mcp.background_worker.write_markdown import process_json_response
from obsidian_rag_mcp.models import JobResult
from obsidian_rag_mcp.rag_core.llm_client import OpenAICompatibleClient
from obsidian_rag_mcp.rag_core.tags import TagCatalog

LOG = logging.getLogger(__name__)

PDF_IMAGE_MAX_LONG_EDGE = 1800
PDF_IMAGE_QUALITY = 78


def process_pdf_to_markdown(
    source_pdf: Path,
    output_md: Path,
    image_dir: Path,
    llm_runtime,
    llm_client: OpenAICompatibleClient,
    tag_catalog: TagCatalog,
) -> JobResult:
    vault_root = output_md if output_md.is_dir() else output_md.parent
    temp_job_dir = image_dir / f"pdf-pages-{uuid4().hex}"

    try:
        page_images = convert_pdf_to_jpg_pages(source_pdf, temp_job_dir)
        if not page_images:
            return JobResult(source_path=source_pdf, success=False, message="no rendered pages", output_doc=None)

        page_summaries: list[str] = []
        total_pages = len(page_images)
        for idx, image in enumerate(page_images, start=1):
            page_prompt = get_pdf_page_extract_prompt(idx, total_pages)
            page_summary = llm_client.chat(
                page_prompt,
                images=[str(image)],
                generation_mode="openai",
                allow_local_fallback=True,
                require_success=True,
            )
            page_summaries.append(f"## Page {idx}\n{page_summary}\n")

        reduced_summary = llm_client.chat(
            get_pdf_reduce_prompt("\n".join(page_summaries)),
            generation_mode="openai",
            allow_local_fallback=True,
            require_success=True,
        )

        full_content = "\n".join(page_summaries)
        tags = _choose_tags(full_content + "\n" + reduced_summary, llm_client, tag_catalog)


        dir_structure = ",".join(
            str(p.relative_to(vault_root))
            for p in vault_root.rglob("*")
            if p.is_dir() and "z.rawdata" not in str(p)
        )

        prompt = get_pdf_note_json_prompt(
            ", ".join(tags),
            full_content,
            reduced_summary,
            dir_structure,
            source_pdf,
        )

        json_response = llm_client.chat(
            prompt,
            generation_mode="openai",
            allow_local_fallback=True,
            require_success=True,
        )

        note_path, parsed_tags = process_json_response(json_response, vault_root)
        _ensure_backlink(note_path, source_pdf)
        final_tags = parsed_tags if parsed_tags else tags
        tag_catalog.persist_doc_tags(str(note_path), final_tags)

        return JobResult(source_path=source_pdf, success=True, message="pdf processed", output_doc=note_path)

    except Exception as exc:
        LOG.exception("pdf pipeline failed")
        return JobResult(source_path=source_pdf, success=False, message=str(exc))
    finally:
        shutil.rmtree(temp_job_dir, ignore_errors=True)


def convert_pdf_to_jpg_pages(pdf_path: Path, image_dir: Path) -> list[Path]:
    if pdfium is None:
        raise RuntimeError("pypdfium2 is not installed; cannot render PDF pages")

    image_dir.mkdir(parents=True, exist_ok=True)
    pdf = pdfium.PdfDocument(str(pdf_path))
    pages: list[Path] = []
    for i in range(len(pdf)):
        page = pdf[i]
        bitmap = page.render(scale=2)
        pil_image = bitmap.to_pil().convert("L")
        pil_image = _resize_preserving_long_edge(pil_image, PDF_IMAGE_MAX_LONG_EDGE)

        out = image_dir / f"{pdf_path.stem}-page-{i+1}.jpg"
        pil_image.save(out, format="JPEG", quality=PDF_IMAGE_QUALITY, optimize=True, progressive=True)
        pages.append(out)
    return pages


def _resize_preserving_long_edge(image, max_long_edge: int):
    width, height = image.size
    long_edge = max(width, height)
    if long_edge <= max_long_edge:
        return image
    scale = max_long_edge / float(long_edge)
    new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
    return image.resize(new_size, resample=Image.LANCZOS)


def _choose_tags(content: str, llm_client: OpenAICompatibleClient, tag_catalog: TagCatalog) -> list[str]:
    catalog = tag_catalog.store.get_tags()
    catalog_hint = ", ".join(catalog[:30]) if catalog else "(none)"
    raw = llm_client.chat(
        get_pdf_tags_prompt(catalog_hint, content[:6000]),
        generation_mode="openai",
        allow_local_fallback=True,
        require_success=True,
    )
    candidates = [x.strip().lower().replace(" ", "-") for x in raw.split(",") if x.strip()]
    reusable, new_tags = tag_catalog.suggest_reusable(candidates)
    tags = sorted(set(reusable + new_tags))
    return tags[:5] if tags else ["general-knowledge"]


def _build_raw_pdf_backlink(vault_root: Path, raw_pdf_path: Path) -> str:
    rel = raw_pdf_path.resolve().relative_to(vault_root.resolve())
    return f"[[{rel.as_posix()}]]"


def _ensure_backlink(note_path: Path, backlink: str) -> None:
    content = note_path.read_text(encoding="utf-8")
    if backlink in content:
        return
    content = content.rstrip() + f"\n\n## Source\n{backlink}\n"
    note_path.write_text(content, encoding="utf-8")
