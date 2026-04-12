
def get_normalize_to_markdown(tags, raw_content):
    normalize_to_markdown = f'''
# SYSTEM
You are writing a refined knowledge note from a raw transcription.

Think of this as transforming spoken thought into a polished personal knowledge artifact.

Output STRICTLY in valid JSON with the following structure:

{{
  "fileName": "<string>",
  "content": "<markdown string>"
}}

Where:
- "fileName" is a concise, descriptive title derived from the content (no special characters except hyphens or spaces)
- "content" is the full Markdown note

The Markdown inside "content" must follow this structure:

# Title

## 1. Refined Transcript
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
- No EM-Dashes (—) in output
- No content loss
- No fluff
- Output ONLY valid JSON
- Do NOT include explanations, markdown fences, or extra text outside JSON

# USER
data : 
{raw_content}

tags : 
{tags}
            '''

    return normalize_to_markdown

