from __future__ import annotations

import logging
from pathlib import Path

try:
    import pypdfium2 as pdfium
except Exception:  # pragma: no cover
    pdfium = None

from obsidian_rag_mcp.background_worker.llm_runtime import LLMRuntimeManager
from obsidian_rag_mcp.models import JobResult
from obsidian_rag_mcp.rag_core.llm_client import OpenAICompatibleClient
from obsidian_rag_mcp.rag_core.markdown_normalizer import normalize_markdown
from obsidian_rag_mcp.rag_core.tags import TagCatalog

LOG = logging.getLogger(__name__)


def process_pdf_to_markdown(
    source_pdf: Path,
    output_md: Path,
    image_dir: Path,
    llm_runtime: LLMRuntimeManager,
    llm_client: OpenAICompatibleClient,
    tag_catalog: TagCatalog,
) -> JobResult:
    mode = ""
    try:
        page_images = convert_pdf_to_jpg_pages(source_pdf, image_dir)
        mode = llm_runtime.ensure_generation_mode()

        page_summaries: list[str] = []
        for idx, image in enumerate(page_images, start=1):
            prompt = (
                "Extract key readable content from this page image including handwritten text if possible. "
                "Return clean markdown bullets."
            )
            page_summary = llm_client.chat(prompt, images=[str(image)])
            page_summaries.append(f"## Page {idx}\n{page_summary}\n")

        reduced_summary = llm_client.chat(
            "Reduce these per-page summaries into one consolidated summary with major themes and action items:\n\n"
            + "\n".join(page_summaries)
        )
        full_content = "\n".join(page_summaries)
        tags = _choose_tags(full_content + "\n" + reduced_summary, llm_client, tag_catalog)
        normalized = normalize_markdown(full_content, str(source_pdf), reduced_summary, tags)

        output_md.parent.mkdir(parents=True, exist_ok=True)
        output_md.write_text(normalized, encoding="utf-8")
        tag_catalog.persist_doc_tags(str(output_md), tags)
        return JobResult(source_path=source_pdf, success=True, message="pdf processed", output_doc=output_md)
    except Exception as exc:
        LOG.exception("pdf pipeline failed")
        return JobResult(source_path=source_pdf, success=False, message=str(exc))
    finally:
        if mode == "local":
            llm_runtime.eject_local_model()


def convert_pdf_to_jpg_pages(pdf_path: Path, image_dir: Path) -> list[Path]:
    image_dir.mkdir(parents=True, exist_ok=True)
    if pdfium is None:
        placeholder = image_dir / f"{pdf_path.stem}-page-1.jpg"
        placeholder.write_bytes(b"placeholder")
        return [placeholder]

    pdf = pdfium.PdfDocument(str(pdf_path))
    pages: list[Path] = []
    for i in range(len(pdf)):
        page = pdf[i]
        bitmap = page.render(scale=2)
        pil_image = bitmap.to_pil()
        out = image_dir / f"{pdf_path.stem}-page-{i+1}.jpg"
        pil_image.save(out, format="JPEG")
        pages.append(out)
    return pages


def _choose_tags(content: str, llm_client: OpenAICompatibleClient, tag_catalog: TagCatalog) -> list[str]:
    catalog = tag_catalog.store.get_tags()
    catalog_hint = ", ".join(catalog[:30]) if catalog else "(none)"
    prompt = (
        "Choose up to 5 domain tags for this note. Prefer these existing tags when relevant: "
        f"{catalog_hint}. If no existing tag fits, create minimal new tags. "
        "Return a comma-separated list only.\n\n"
        f"CONTENT:\n{content[:6000]}"
    )
    raw = llm_client.chat(prompt)
    candidates = [x.strip().lower().replace(" ", "-") for x in raw.split(",") if x.strip()]
    reusable, new_tags = tag_catalog.suggest_reusable(candidates)
    tags = sorted(set(reusable + new_tags))
    return tags[:5] if tags else ["general-knowledge"]
