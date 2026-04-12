from __future__ import annotations

import json
from typing import Any

from obsidian_rag_mcp.config import AppConfig
from obsidian_rag_mcp.mcp_server.tools import MCPTools


def run_stdio_server(config: AppConfig) -> None:
    """
    Minimal stdio loop for MCP-like usage.
    Input JSON lines:
      {"tool":"reindex_vault_delta"}
      {"tool":"query_vault_context","args":{"query":"...","k":5}}
    """
    tools = MCPTools(config)
    handlers = {
        "reindex_vault_delta": lambda args: tools.reindex_vault_delta(),
        "query_vault_context": lambda args: tools.query_vault_context(args.get("query", ""), int(args.get("k", 5))),
    }

    while True:
        try:
            line = input()
        except EOFError:
            break
        if not line.strip():
            continue
        req = json.loads(line)
        tool = req.get("tool")
        args = req.get("args", {})
        if tool not in handlers:
            print(json.dumps({"error": f"unknown tool {tool}"}))
            continue
        try:
            result = handlers[tool](args)
            print(json.dumps({"ok": True, "result": result}))
        except Exception as exc:
            print(json.dumps({"ok": False, "error": str(exc)}))
