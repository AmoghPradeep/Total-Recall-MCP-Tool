from __future__ import annotations

import base64
import logging
from pathlib import Path

from openai import OpenAI

LOG = logging.getLogger(__name__)


class OpenAICompatibleClient:
    def __init__(self, base_url: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    def chat(
        self,
        prompt: str,
        images: list[str] | None = None,
        generation_mode: str = "openai",
        allow_local_fallback: bool = True,
        require_success: bool = False,
    ) -> str:
        """
        Supported modes:
        - openai: OpenAI first, optionally fallback to local OpenAI-compatible endpoint
        - api/local: local endpoint first, optionally fallback to OpenAI
        """
        errors: list[Exception] = []

        if generation_mode in {"openai", "openai_first"}:
            try:
                return self._chat_openai(prompt, images)
            except Exception as exc:
                errors.append(exc)
                LOG.warning("OpenAI generation failed: %s", exc)
                if allow_local_fallback:
                    try:
                        return self._chat_local(prompt, images)
                    except Exception as local_exc:
                        errors.append(local_exc)
                        LOG.warning("Local fallback generation failed: %s", local_exc)
        else:
            try:
                return self._chat_local(prompt, images)
            except Exception as exc:
                errors.append(exc)
                LOG.warning("Local generation failed: %s", exc)
                if allow_local_fallback:
                    try:
                        return self._chat_openai(prompt, images)
                    except Exception as openai_exc:
                        errors.append(openai_exc)
                        LOG.warning("OpenAI fallback generation failed: %s", openai_exc)

        if require_success:
            raise RuntimeError(f"Generation failed across providers: {errors}")
        return prompt[:2000]

    def _chat_openai(self, prompt: str, images: list[str] | None) -> str:
        client = OpenAI()
        response = client.responses.create(
            model=self.model,
            input=self._build_input(prompt, images),
        )
        return response.output_text

    def _chat_local(self, prompt: str, images: list[str] | None) -> str:
        client = OpenAI(base_url=self.base_url, api_key="local")
        response = client.responses.create(
            model=self.model,
            input=self._build_input(prompt, images),
        )
        return response.output_text

    def _build_input(self, prompt: str, images: list[str] | None):
        if not images:
            return prompt

        content: list[dict] = [{"type": "input_text", "text": prompt}]
        for image_path in images:
            url = self._to_data_url(Path(image_path))
            content.append({"type": "input_image", "image_url": url})

        return [{"role": "user", "content": content}]

    @staticmethod
    def _to_data_url(path: Path) -> str:
        mime = "image/jpeg"
        if path.suffix.lower() == ".png":
            mime = "image/png"
        data = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:{mime};base64,{data}"


def transcribe_audio_fallback(audio_path: Path) -> str:
    return f"Transcribed text placeholder for {audio_path.name}."
