## Context

The current note-generation flow gives the LLM control over four things at once: file name, destination directory, note body structure, and visible provenance formatting. That creates two classes of failures.

First, the writer trusts any vault-relative directory that is not absolute or traversing, so a model-supplied `relativePath` such as `z.rawdata/text` is treated as valid output. Audio and text pipelines also pass directory hints that include `z.rawdata`, which makes that mistake more likely.

Second, provenance is split between the prompt and the pipeline. The prompts ask the model to emit a `Resources` section, while the page-document pipeline may later append or replace a `Source` section. The result is duplicate sections, inconsistent headings, and visible raw-path links. Audio also passes a temporary compressed-file path into prompt context, which is not a stable vault reference.

This change is cross-cutting because it touches prompt wording, path validation, source rendering, and every normalized-note-producing ingestion flow.

## Goals / Non-Goals

**Goals:**
- Prevent generated markdown notes from being written into `z.rawdata` or other reserved system folders.
- Remove the duplicated visible title by omitting the top-level H1 from generated note bodies.
- Constrain note placement to a broad, human-readable taxonomy with at most three directory levels.
- Produce exactly one canonical source section with aliased Obsidian links and stable vault-backed targets.
- Make output behavior consistent across audio, text, PDF, and image-folder ingestion.

**Non-Goals:**
- Rewriting or migrating previously generated notes already stored in user vaults.
- Changing chunking, embeddings, retrieval ranking, or MCP tool behavior.
- Building a user-configurable taxonomy editor in this change.
- Replacing the LLM-driven note normalization approach with a deterministic non-LLM formatter.

## Decisions

1. Move provenance rendering from the prompt contract into system-owned post-processing.
- The model should still generate the normalized note content and suggested metadata, but the system should own the final source section.
- Prompts will stop instructing the model to create `Resources`, `Source`, or `Sources` sections. After JSON parsing, the system will canonicalize the body and inject a single `## Sources` section.
- Alternative considered: keep provenance in the prompt and tighten wording. Rejected because the current duplicate-section bug exists specifically because prompt compliance is not reliable enough.

2. Canonicalize generated note bodies before the final write.
- The write path should strip a top-level H1 title if present and remove any model-generated provenance sections (`## Resources`, `## Source`, or `## Sources`) before appending the canonical `## Sources` block.
- This preserves a consistent note shape even when the model only partially follows the prompt.
- Alternative considered: rely on prompt changes alone. Rejected because prompt-only fixes reduce error rates but do not harden the system.

3. Enforce a bounded destination taxonomy at write time and bias the prompt toward the same policy.
- Eligible output roots should be limited to a small human-oriented taxonomy such as `People`, `Projects`, `Areas`, `Topics`, and `References`.
- `relativePath` must stay within those roots and contain at most three path segments total. Invalid, reserved, or overly deep paths should fall back to the default import directory.
- A shared directory-hint builder should list only eligible non-reserved directories so the model sees the same contract that the writer enforces.
- Alternative considered: allow any vault-relative directory except `z.rawdata`. Rejected because it still allows over-specific or aesthetically poor folder trees.

4. Use aliased wikilinks for provenance labels.
- Source links should preserve the actual vault target path while showing readable labels such as `Original audio`, `Original PDF`, `Original text`, or `Page 1`.
- This keeps provenance usable without exposing raw storage paths as visible body text.
- Alternative considered: plain markdown links or raw wikilinks. Rejected because Obsidian alias wikilinks solve the formatting issue directly and match the rest of the vault model.

5. Use staged raw vault assets as the source of truth for provenance.
- Pipelines should build source-link labels from the copied raw asset path inside `z.rawdata`, not from temporary files or transient compression outputs.
- This is especially important for audio, where the current prompt context can reference a temp file rather than the staged raw source.
- Alternative considered: keep temp-path-based prompt context for audio and fix only visible output. Rejected because it leaves unstable provenance in the generation pipeline.

6. Keep file naming separate from visible note headings.
- The prompt contract should ask for a concise human-readable file name, while the written markdown body must not repeat that title as a top-level heading.
- The writer should continue sanitizing unsafe characters and duplicate filename collisions.
- Alternative considered: preserve the current H1 heading and just improve the name. Rejected because it keeps the duplicate-title problem the user explicitly wants removed.

## Risks / Trade-offs

- [A stricter taxonomy may send ambiguous notes to the fallback directory more often] -> Mitigation: log fallback reasons clearly and expose only eligible existing directories to the model.
- [Canonical post-processing may remove a section the model intended for non-provenance content if it uses reserved headings loosely] -> Mitigation: target only the reserved provenance headings and keep the canonical note body otherwise intact.
- [Aliased links improve aesthetics but hide the literal path from casual readers] -> Mitigation: the real target path remains encoded in the wikilink, and users can inspect it in Obsidian when needed.
- [Cross-pipeline consistency work touches multiple modules at once] -> Mitigation: centralize helpers for eligible directories, note canonicalization, and source-link formatting rather than duplicating fixes.

## Migration Plan

1. Add shared output-policy helpers for eligible directory discovery, reserved-path validation, note-body canonicalization, and aliased source-link rendering.
2. Update prompt builders and all normalized-note-producing pipelines to use the shared policy and stable raw-source references.
3. Extend integration and path-safety tests to cover reserved directories, duplicate source sections, aliased provenance links, and taxonomy bounds.
4. Update runbook or related operational documentation only if the new visible note-location policy needs to be explained.

## Open Questions

None.
