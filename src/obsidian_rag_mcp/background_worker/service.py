from __future__ import annotations

import logging
import time
from pathlib import Path

from obsidian_rag_mcp.background_worker.audio_pipeline import process_audio_to_markdown
from obsidian_rag_mcp.background_worker.llm_runtime import ASRRuntimeManager, LLMRuntimeManager
from obsidian_rag_mcp.background_worker.pdf_pipeline import process_pdf_to_markdown
from obsidian_rag_mcp.background_worker.queue import DurableJobQueue
from obsidian_rag_mcp.background_worker.watchers import scan_and_enqueue
from obsidian_rag_mcp.config import AppConfig
from obsidian_rag_mcp.rag_core.embeddings import EmbeddingService
from obsidian_rag_mcp.rag_core.indexing import index_markdown_document
from obsidian_rag_mcp.rag_core.llm_client import OpenAICompatibleClient
from obsidian_rag_mcp.rag_core.tags import TagCatalog
from obsidian_rag_mcp.rag_core.vector_store.sqlite_store import SQLiteVectorStore

LOG = logging.getLogger(__name__)


class BackgroundWorker:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.queue = DurableJobQueue(config.queue_path)
        self.vector_store = SQLiteVectorStore(config.db_path)
        self.embeddings = EmbeddingService(config.models.llm_service_url, config.models.embedding_model)
        self.llm_runtime = LLMRuntimeManager(config.models.llm_service_url, config.models.generation_model)
        self.asr_runtime = ASRRuntimeManager(config.models.asr_model)
        self.llm_client = OpenAICompatibleClient(config.models.llm_service_url, config.models.generation_model)
        self.tag_catalog = TagCatalog(self.vector_store)

    def scan_once(self) -> dict[str, int]:
        return scan_and_enqueue(self.config.audio_watch_path, self.config.pdf_watch_path, self.queue)

    def process_queue_once(self) -> dict[str, int]:
        jobs = self.queue.pop_all()
        metrics = {"processed": 0, "errors": 0, "indexed_chunks": 0}
        for job in jobs:
            source = Path(job.source_path)
            output_name = source.stem + ".md"
            out_path = self.config.vault_path / output_name
            result = self._run_job_with_retry(job.job_type, source, out_path)
            if result.success and result.output_doc:
                text = result.output_doc.read_text(encoding="utf-8")
                count = index_markdown_document(
                    result.output_doc,
                    text,
                    self.embeddings,
                    self.vector_store,
                    chunk_size=self.config.chunking.chunk_size,
                    chunk_overlap=self.config.chunking.chunk_overlap,
                )
                metrics["indexed_chunks"] += count
                metrics["processed"] += 1
            else:
                metrics["errors"] += 1
        return metrics

    def run_forever(self, poll_seconds: float = 2.0) -> None:
        while True:
            queued = self.scan_once()
            metrics = self.process_queue_once()
            LOG.info("scan=%s metrics=%s", queued, metrics)
            time.sleep(poll_seconds)

    def _run_job_with_retry(self, job_type: str, source: Path, out_path: Path, retries: int = 2):
        image_dir = self.config.vault_path / ".tmp_pages"
        last_result = None
        for attempt in range(retries + 1):
            if job_type == "audio":
                last_result = process_audio_to_markdown(
                    source_audio=source,
                    output_md=out_path,
                    asr_runtime=self.asr_runtime,
                    llm_runtime=self.llm_runtime,
                    llm_client=self.llm_client,
                    tag_catalog=self.tag_catalog,
                )
            else:
                last_result = process_pdf_to_markdown(
                    source_pdf=source,
                    output_md=out_path,
                    image_dir=image_dir,
                    llm_runtime=self.llm_runtime,
                    llm_client=self.llm_client,
                    tag_catalog=self.tag_catalog,
                )
            if last_result.success:
                return last_result
            LOG.warning("Job failed type=%s source=%s attempt=%s", job_type, source, attempt + 1)
        return last_result
