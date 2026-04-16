from __future__ import annotations

import logging
from pathlib import Path

from total_recall.background_worker.output_policy import build_aliased_vault_link, build_directory_hint
from total_recall.background_worker.system_prompts import get_normalize_text_to_markdown
from total_recall.background_worker.write_markdown import process_json_response
from total_recall.models import JobResult
from total_recall.rag_core.llm_client import OpenAICompatibleClient
from total_recall.rag_core.tags import TagCatalog

LOG = logging.getLogger(__name__)


def process_text_to_markdown(
    source_text: Path,
    output_md: Path,
    llm_client: OpenAICompatibleClient,
    tag_catalog: TagCatalog,
) -> JobResult:
    try:
        LOG.info("Starting text pipeline source=%s", source_text)
        vault_root = output_md if output_md.is_dir() else output_md.parent
        raw_content = source_text.read_text(encoding="utf-8")
        LOG.info("Loaded text source source=%s char_count=%s", source_text, len(raw_content))

        tags = tag_catalog.store.get_tags()
        LOG.debug("Normalizing text markdown source=%s known_tag_count=%s", source_text, len(tags))
        source_link = build_aliased_vault_link(vault_root, source_text, "Original Text")
        prompt = get_normalize_text_to_markdown(
            ", ".join(tags),
            raw_content,
            build_directory_hint(vault_root),
            source_link,
        )
        json_response = llm_client.chat(prompt)

        output_md, tags = process_json_response(json_response, vault_root, source_links=[source_link])
        tag_catalog.persist_doc_tags(str(output_md), tags)
        LOG.info("Completed text pipeline source=%s output_doc=%s tag_count=%s", source_text, output_md, len(tags))
        return JobResult(source_path=source_text, success=True, message="text processed", output_doc=output_md)
    except Exception as exc:
        LOG.exception("Text pipeline failed source=%s", source_text)
        return JobResult(source_path=source_text, success=False, message=str(exc))
