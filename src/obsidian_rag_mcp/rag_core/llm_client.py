from __future__ import annotations

import logging
from pathlib import Path
from openai import OpenAI

import httpx

from obsidian_rag_mcp.rag_core.vector_store import SQLiteVectorStore

LOG = logging.getLogger(__name__)


class OpenAICompatibleClient:
    def __init__(self, base_url: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    def chat(self, prompt: str, images: list[str] | None = None, generation_mode: str = 'openai') -> str:

        if generation_mode == 'openai':
            client = OpenAI()

            model = "gpt-5.4-mini"
            response = client.responses.create(
                model=model,
                input=prompt
            )
            return response.output_text

        else:
            try:
                client = OpenAI(base_url=self.base_url)

                response = client.responses.create(
                    input=prompt
                )

                return response.output_text
            except Exception as e:
                LOG.error(e)
                return self.chat(prompt, images, 'openai')


def transcribe_audio_fallback(audio_path: Path) -> str:
    return f"Transcribed text placeholder for {audio_path.name}."
