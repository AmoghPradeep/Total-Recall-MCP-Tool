## 1. Output Policy

- [x] 1.1 Add shared output-policy helpers that exclude reserved vault roots, enforce the bounded destination taxonomy, and fall back safely for invalid or overly deep `relativePath` values.
- [x] 1.2 Update markdown writing and canonicalization so generated note bodies omit the top-level H1 title and always contain at most one system-owned `## Sources` section.

## 2. Prompt And Pipeline Alignment

- [x] 2.1 Update normalized-note prompts to request concise human-readable filenames, forbid title headings in `content`, remove model-owned provenance sections, and describe the bounded folder taxonomy.
- [x] 2.2 Update audio, text, PDF, and image-folder flows to use shared eligible-directory hints and stable vault-backed source references instead of transient temp paths.
- [x] 2.3 Add aliased Obsidian source-link formatting for single-source and multi-source notes so visible labels stay readable while targets remain exact.

## 3. Verification

- [x] 3.1 Add unit and integration coverage for reserved-directory blocking, taxonomy depth limits, title stripping, duplicate source-section cleanup, and aliased source-link rendering.
- [x] 3.2 Update any runbook or behavior documentation needed to reflect the new generated-note placement and provenance rules.
