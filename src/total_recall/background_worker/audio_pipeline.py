from __future__ import annotations

import logging
from pathlib import Path

from total_recall.background_worker.file_utils import compress_for_asr_tempdir
from total_recall.background_worker.output_policy import build_aliased_vault_link, build_directory_hint
from total_recall.background_worker.system_prompts import get_normalize_to_markdown
from total_recall.background_worker.write_markdown import process_json_response
from total_recall.models import JobResult
from total_recall.rag_core.llm_client import OpenAICompatibleClient
from total_recall.rag_core.tags import TagCatalog

LOG = logging.getLogger(__name__)


def process_audio_to_markdown(
    source_audio: Path,
    output_md: Path,
    llm_client: OpenAICompatibleClient,
    tag_catalog: TagCatalog,
    transcription_model: str,
) -> JobResult:
    try:
        LOG.info("Starting audio pipeline source=%s transcription_model=%s", source_audio, transcription_model)
        vault_root = output_md if output_md.is_dir() else output_md.parent
        raw_source = source_audio
        transcription_source = Path(compress_for_asr_tempdir(raw_source))
        LOG.debug("Prepared temporary audio source path=%s", transcription_source)
        transcript = llm_client.transcribe_audio(transcription_source, transcription_model)
        LOG.info("Completed audio transcription source=%s transcript_chars=%s", raw_source, len(transcript))

        tags = tag_catalog.store.get_tags()
        source_link = build_aliased_vault_link(vault_root, raw_source, "Original Audio")
        LOG.debug("Normalizing audio markdown source=%s known_tag_count=%s", raw_source, len(tags))
        prompt = get_normalize_to_markdown(
            ", ".join(tags),
            transcript,
            build_directory_hint(vault_root),
            source_link,
        )
        json_response = llm_client.chat(prompt)

        output_md, tags = process_json_response(json_response, vault_root, source_links=[source_link])
        tag_catalog.persist_doc_tags(str(output_md), tags)
        LOG.info("Completed audio pipeline source=%s output_doc=%s tag_count=%s", raw_source, output_md, len(tags))
        return JobResult(source_path=raw_source, success=True, message="audio processed", output_doc=output_md)
    except Exception as exc:
        LOG.exception("Audio pipeline failed source=%s", source_audio)
        return JobResult(source_path=source_audio, success=False, message=str(exc))
