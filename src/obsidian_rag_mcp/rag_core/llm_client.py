from __future__ import annotations

import logging
from pathlib import Path

import httpx

LOG = logging.getLogger(__name__)


class OpenAICompatibleClient:
    def __init__(self, base_url: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    def chat(self, prompt: str, images: list[str] | None = None) -> str:
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
        }
        if images:
            payload["messages"][0]["content"] = prompt + "\n\n" + "\n".join(images)
        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(f"{self.base_url}/v1/chat/completions", json=payload)
            if resp.status_code < 400:
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        except Exception as exc:
            LOG.warning("LLM API call failed, using fallback generation: %s", exc)
        return prompt[:2000]


def transcribe_audio_fallback(audio_path: Path) -> str:
    return f"Transcribed text placeholder for {audio_path.name}."
