"""
app/analysis/summarizer.py — Summarizes a document using Gemini.

CONCEPT: Prompt Engineering
  We're not just calling an API — we're writing a carefully crafted prompt
  that tells Gemini exactly what we want. The quality of the output depends
  heavily on how well you describe the task in the prompt.

  Key prompt-writing tips used here:
    1. Give a role: "provide a clear and concise summary"
    2. Give a constraint: "approximately {max_words} words"
    3. Give focus: "main ideas, key points, and important conclusions"
    4. Clearly label the input and output sections
"""

import google.generativeai as genai

from config import GEMINI_API_KEY, GEMINI_MODEL

# Configure Gemini and create a reusable model instance
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(GEMINI_MODEL)


def summarize(text: str, max_words: int = 200) -> str:
    """
    Generate a concise summary of the document text.

    Args:
        text:      The full extracted document text.
        max_words: Target word count for the summary (default 200).

    Returns:
        A string containing the summary.
    """
    if not text.strip():
        return "No text found to summarize."

    # Gemini 1.5 Flash has a 1M token context window, but very long texts
    # can be slow. We cap at ~30,000 chars (~7,500 words) which covers most
    # typical business and academic documents.
    truncated = text[:30_000] if len(text) > 30_000 else text

    prompt = f"""Please provide a clear and concise summary of the following document in approximately {max_words} words.

Focus on:
- The main idea or purpose of the document
- Key points and arguments
- Important conclusions or outcomes

Document:
{truncated}

Summary:"""

    response = model.generate_content(prompt)
    return response.text.strip()
