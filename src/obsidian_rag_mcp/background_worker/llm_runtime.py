from __future__ import annotations

import logging
import time

import httpx

LOG = logging.getLogger(__name__)


class LLMRuntimeManager:
    def __init__(self, service_url: str, model_name: str) -> None:
        self.service_url = service_url.rstrip("/")
        self.model_name = model_name
        self.local_model_loaded = False

    def service_is_healthy(self) -> bool:
        try:
            with httpx.Client(timeout=2.0) as client:
                resp = client.get(f"{self.service_url}/v1/models")
            return resp.status_code < 400
        except Exception:
            return False

    def ensure_generation_mode(self) -> str:
        if self.service_is_healthy():
            return "api"
        self.load_local_model()
        return "local"

    def load_local_model(self) -> None:
        if self.local_model_loaded:
            return
        LOG.info("Loading local LLM model %s", self.model_name)
        time.sleep(0.05)
        self.local_model_loaded = True

    def eject_local_model(self) -> None:
        if not self.local_model_loaded:
            return
        LOG.info("Ejecting local LLM model %s", self.model_name)
        self.local_model_loaded = False


class ASRRuntimeManager:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self.loaded = False

    def load(self) -> None:
        self.loaded = True

    def eject(self) -> None:
        self.loaded = False
