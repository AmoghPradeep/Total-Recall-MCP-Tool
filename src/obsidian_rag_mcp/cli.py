from __future__ import annotations

import sys

from obsidian_rag_mcp.background_worker.service import BackgroundWorker
from obsidian_rag_mcp.config import load_config
from obsidian_rag_mcp.logging_utils import setup_logging
from obsidian_rag_mcp.mcp_server.server import run_stdio_server


def run_background() -> None:
    cfg = load_config()
    setup_logging(cfg.log_level)
    worker = BackgroundWorker(cfg)
    worker.run_forever()


def run_mcp_server() -> None:
    cfg = load_config()
    setup_logging(cfg.log_level)
    run_stdio_server(cfg)


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "mcp"
    if command == "background":
        run_background()
    else:
        run_mcp_server()
