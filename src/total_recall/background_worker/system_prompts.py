from __future__ import annotations


def _shared_output_contract(dir_structure, source_reference_block: str) -> str:
    return f'''
Output STRICTLY in valid JSON with the following structure:

{{
  "fileName": "<string>",
  "relativePath": "<string>",
  "content": "<markdown string>",
  "tags": ["tag1", "tag2", "tag3"]
}}

Where:
- "fileName" is a concise, human-readable note name in Title Case, ideally 2 to 6 words, with no special characters except hyphens or spaces
- "relativePath" refers to a vault-relative DIRECTORY only.
  Directory policy for "relativePath":
  - MUST start with exactly one of: `People`, `Projects`, `Areas`, `Topics`, `References`
  - MUST contain 1 to 3 directory segments total
  - MUST stay broad and reusable for future notes
  - MUST prefer an existing directory from the provided structure when it is a good fit
  - MUST NOT use reserved or internal folders such as `z.rawdata`, `.obsidian`, or `.trash`
  IMPORTANT path constraints for "relativePath":
  - MUST be relative (never absolute)
  - MUST NOT start with drive letters like `C:\\` or malformed forms like `C--Users`
  - MUST NOT start with `/`, `\\`, or `//`
  - MUST NOT contain `..` or `.` traversal segments
  - MUST NOT include the file name
- "content" is the full Markdown note
- "tags" are the same tags mentioned inside the file contents.

Directory Structure:
{{ {dir_structure} }}

The Markdown inside "content" must follow this structure:
## 1. Transcript
Transform the source into clear, structured writing:
- Preserve all ideas and nuances
- Remove obvious noise, repetition, and formatting debris
- Rewrite in a calm, precise, and intellectual tone
- Make it feel like a well-maintained notebook entry
- Use paragraphs and light structure where helpful
- Do not summarize

## 2. Summary & Takeaways
Distill the note into:
- Core ideas
- Important insights
- Practical implications or actions

Be concise and structured.

## 3. Tags
- Prefer existing tags from input
- Add only if necessary
- Keep tags broad (e.g., #learning, #psychology, #business)
- Avoid niche or overly specific tags

Do NOT include a top-level `#` title heading.
Do NOT include any `## Resources`, `## Source`, or `## Sources` section.
The system will add the canonical source links after generation.

Source references for context only:
{source_reference_block}

Constraints:
- No hallucinations
- No EM-Dashes in output
- No content loss
- No fluff
- Output ONLY valid JSON
- Do NOT include explanations, markdown fences, or extra text outside JSON
'''


def get_normalize_to_markdown(tags, raw_content, dir_structure, source_reference):
    return f'''
# SYSTEM
You are writing a refined knowledge note from a raw transcription.

Think of this as transforming spoken thought into a polished personal knowledge artifact.
{_shared_output_contract(dir_structure, source_reference)}

# USER
data :
{raw_content}

tags :
{tags}
            '''


def get_normalize_text_to_markdown(tags, raw_content, dir_structure, source_reference):
    return f'''
# SYSTEM
You are writing a refined knowledge note from a raw text file.

Think of this as transforming rough source material into a polished personal knowledge artifact.
The input may already contain markdown, fragments, headings, bullets, or lightly structured notes.
Preserve the substance, clean the structure, and normalize it into the same note shape used by the existing ingestion flows.
{_shared_output_contract(dir_structure, source_reference)}

# USER
data :
{raw_content}

tags :
{tags}
            '''


def get_pdf_page_extract_prompt(page_number: int, total_pages: int) -> str:
    return f'''
# SYSTEM
You are extracting content from a handwritten-notes PDF page image.

Context: page {page_number} of {total_pages}.

Instructions:
- Extract all readable text faithfully.
- Preserve structure with bullets/headings/checklists where visible.
- Mark uncertain words with [unclear].
- Do not hallucinate missing text.
- Keep output concise markdown only.

Output format:
- Return markdown content for this page only.
- No explanations or code fences.
'''


def get_pdf_reduce_prompt(page_summaries: str) -> str:
    return f'''
# SYSTEM
You are reducing per-page extracted notes into a consolidated document summary.

Instructions:
- Merge duplicate ideas.
- Preserve key action items, decisions, and themes.
- Keep it concise and structured.
- Do not invent content.

# USER
Per-page extracted notes:
{page_summaries}
'''


def get_pdf_tags_prompt(existing_tags: str, content: str) -> str:
    return f'''
# SYSTEM
Choose up to 5 domain tags for this note.
Prefer existing tags where suitable.
Only create a new tag if absolutely necessary.
Return ONLY a comma-separated list.

Existing tags:
{existing_tags}

# USER
{content}
'''


def get_page_document_note_json_prompt(tags, extracted_content, summary, dir_structure, source_resources):
    return f'''
# SYSTEM
Create a normalized Obsidian markdown note from page-image transcription.

You are given the raw OCR transcript of a handwritten note extracted from one or more page images.

Your task is to turn that noisy transcript into a clean, polished, well-structured knowledge note.

Important context:
- The source was handwritten, so the OCR may contain spelling mistakes, broken sentences, missing punctuation, duplicated fragments, incorrect word boundaries, and misread words.
- The original writing may be incomplete, loosely structured, or ambiguous.
- Treat the input as rough personal thinking that needs light reconstruction, not as a formal document.

Your goals:
1. Infer the most likely topic and intended meaning from the transcript.
2. Correct obvious OCR and spelling errors where the intended meaning is reasonably clear.
3. Reorganize the content into a coherent, readable note with clear structure.
4. Preserve the original ideas, intent, and level of detail as much as possible.
5. Add only the minimum connective language needed to make the note understandable and fluent.

Rules:
- Do not invent facts, examples, citations, or explanations that are not supported by the transcript.
- Do not significantly expand the content.
- Do not over-formalize the writing; keep it faithful to the original note-taking style, but cleaner and clearer.
- If a passage is too ambiguous to confidently resolve, preserve it in the most plausible form rather than hallucinating.
- Remove obvious OCR garbage, repeated fragments, and meaningless artifacts.
- Normalize formatting, grammar, and punctuation.
{_shared_output_contract(dir_structure, source_resources)}

# USER
Extracted content:
{extracted_content}

Summary:
{summary}

Tags:
{tags}
'''


def get_pdf_note_json_prompt(tags, extracted_content, summary, dir_structure, raw_pdf_backlink):
    return get_page_document_note_json_prompt(tags, extracted_content, summary, dir_structure, raw_pdf_backlink)
