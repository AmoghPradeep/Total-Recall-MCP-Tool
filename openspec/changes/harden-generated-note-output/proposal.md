## Why

Generated notes currently rely too heavily on unconstrained LLM output for destination folders, visible note structure, and provenance rendering. That leads to notes being written into `z.rawdata`, duplicate title and source sections, and ugly raw-path backlinks, so the output needs a stricter system-owned contract now.

## What Changes

- Reserve raw-data and other internal vault folders for source storage only, and block generated markdown notes from being written there even when the model requests those paths.
- Replace the current loose note-output contract with a canonical generated-note shape that omits the top-level title heading, uses a single system-owned `## Sources` section, and keeps note identity in the file name.
- Constrain note placement to a broad human-oriented folder taxonomy with at most three levels of hierarchy and safe fallback behavior for invalid, reserved, or overly specific destinations.
- Render source provenance as aliased Obsidian wikilinks with readable labels instead of exposing raw visible paths in note bodies.
- Align audio, text, PDF, and image-folder generation flows on the same directory filtering, source-link formatting, and output validation behavior.
- Add tests for reserved-directory blocking, canonical source-section rendering, bounded directory selection, and stable source-link generation.

## Capabilities

### New Capabilities
- `generated-note-output-governance`: Standardize where generated notes can be written, how their bodies are structured, how filenames are chosen, and how source provenance is rendered across all ingestion pipelines.

### Modified Capabilities

## Impact

- Affected code: `src/total_recall/background_worker/system_prompts.py`, `src/total_recall/background_worker/write_markdown.py`, audio/text/page-document pipeline helpers, and related integration/path-safety tests.
- API impact: no MCP protocol change is required.
- Operational impact: newly generated notes will land under a bounded knowledge taxonomy, use one canonical source section, and keep raw assets isolated to `z.rawdata`.
