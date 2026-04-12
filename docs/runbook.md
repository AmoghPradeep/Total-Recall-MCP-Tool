# Runbook

## Configuration

Use environment variables with prefix `OBRAG_`.

- `OBRAG_VAULT_PATH`
- `OBRAG_AUDIO_WATCH_PATH`
- `OBRAG_PDF_WATCH_PATH`
- `OBRAG_DB_PATH`
- `OBRAG_MANIFEST_PATH`
- `OBRAG_QUEUE_PATH`
- `OBRAG_MODELS__LLM_SERVICE_URL` (default `http://localhost:1234`)
- `OBRAG_CHUNKING__CHUNK_SIZE` (default `800`)
- `OBRAG_CHUNKING__CHUNK_OVERLAP` (default `120`)

## Start background worker

```powershell
obsidian-rag-background
```

## Start MCP tool server

```powershell
obsidian-rag-mcp-server
```

Send JSON lines to stdin:

```json
{"tool":"reindex_vault_delta"}
{"tool":"query_vault_context","args":{"query":"what did we discuss about transformers?","k":5}}
```

## Windows startup task

```powershell
.\scripts\register-startup-task.ps1
```

## Recovery

- Rebuild vectors: delete `manifest.json`, then run `reindex_vault_delta`.
- If tags drift: clear `doc_tags` and `tags` tables in `rag.sqlite3` and re-run indexing.
- If local LLM service is down on `localhost:1234`, worker falls back to local model load/eject flow.
