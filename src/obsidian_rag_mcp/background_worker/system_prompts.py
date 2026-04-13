from __future__ import annotations


def get_normalize_to_markdown(tags, raw_content, dir_structure, raw_file_path):
    normalize_to_markdown = f'''
# SYSTEM
You are writing a refined knowledge note from a raw transcription.

Think of this as transforming spoken thought into a polished personal knowledge artifact.

Output STRICTLY in valid JSON with the following structure:

{{
  "fileName": "<string>",
  "relativePath": "<string>",
  "content": "<markdown string>",
  "tags": ["tag1", "tag2", "tag3"]
}}

Where:
- "fileName" is a concise, descriptive title derived from the content (no special characters except hyphens or spaces)
- "relativePath" refers to a vault-relative DIRECTORY only. Use existing directories where possible.
  IMPORTANT path constraints for "relativePath":
  - MUST be relative (never absolute)
  - MUST NOT start with drive letters like `C:\\` or malformed forms like `C--Users`
  - MUST NOT start with `/`, `\\`, or `//`
  - MUST NOT contain `..` or `.` traversal segments
  - MUST NOT include the file name
  - If unsure, use: `inbox/imported`
- "content" is the full Markdown note
- "tags" are the same tags mentioned inside the file contents.

Directory Structure:
{{ {dir_structure} }}
The Markdown inside "content" must follow this structure:

# Title

## 1. Transcript
Transform the transcription into clear, structured writing:
- Preserve all ideas and nuances
- Remove verbal noise and repetition
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

Constraints:
- No hallucinations
- No EM-Dashes in output
- No content loss
- No fluff
- Output ONLY valid JSON
- Do NOT include explanations, markdown fences, or extra text outside JSON

## Resource
- backlink to original raw file

{raw_file_path}
# USER
data :
{raw_content}

tags :
{tags}
            '''

    return normalize_to_markdown


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


def get_pdf_note_json_prompt(tags, extracted_content, summary, dir_structure, raw_pdf_backlink):
    return f'''
# SYSTEM
Create a normalized Obsidian markdown note for PDF-derived content.
Output STRICTLY valid JSON:

{{
  "fileName": "<string>",
  "relativePath": "<string>",
  "content": "<markdown string>",
  "tags": ["tag1", "tag2"]
}}

Path constraints for "relativePath":
- MUST be vault-relative only.
- MUST NOT be absolute, UNC, rooted, or include traversal segments.
- MUST NOT contain file name.
- If unsure: use `inbox/imported`.

Markdown requirements for "content":
- Include sections:
  1) # Title
  2) ## Extracted Notes
  3) ## Summary
  4) ## Source
- In Source section, include this exact backlink: {raw_pdf_backlink}
- Preserve fidelity to extracted content.
- No hallucinations.

Directory Structure:
{{ {dir_structure} }}

# USER
Extracted content:
{extracted_content}

Summary:
{summary}

Tags:
{tags}
'''
