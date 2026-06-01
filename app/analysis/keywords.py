"""
app/analysis/keywords.py — Extracts keywords and topics from a document.

DIFFERENCE between keywords and topics:
  - Keywords : specific, granular terms  → "neural networks", "backpropagation"
  - Topics   : broad themes              → "Machine Learning", "AI Ethics"

We ask Gemini to return both in a structured format, then parse the response
into clean Python lists. Structured output parsing is a common pattern when
working with LLMs that don't natively support JSON mode.
"""

import google.generativeai as genai

from config import GEMINI_API_KEY, GEMINI_MODEL

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(GEMINI_MODEL)


def extract_keywords(text: str, num_keywords: int = 10) -> dict:
    """
    Extract keywords and high-level topics from the document.

    Args:
        text:         The document text.
        num_keywords: How many keywords to extract (default 10).

    Returns:
        {
          "keywords": ["keyword1", "keyword2", ...],
          "topics":   ["Topic A", "Topic B", ...]
        }
    """
    if not text.strip():
        return {"keywords": [], "topics": []}

    # Use a 20k char window — enough for a dense document
    truncated = text[:20_000] if len(text) > 20_000 else text

    # We ask for a rigid output format so our parser below is reliable.
    # This is called "few-shot prompting with format constraints".
    prompt = f"""Analyze the following document and extract:
1. The top {num_keywords} most important keywords or key phrases (specific terms)
2. The top 3-5 main topics or themes (broad categories)

Respond in EXACTLY this format (no extra lines):
KEYWORDS: keyword1, keyword2, keyword3
TOPICS: topic1, topic2, topic3

Document:
{truncated}"""

    response = model.generate_content(prompt)
    result_text = response.text.strip()

    # ── Parse the structured response ────────────────────────────────────────
    keywords: list[str] = []
    topics: list[str] = []

    for line in result_text.split("\n"):
        line = line.strip()
        if line.startswith("KEYWORDS:"):
            raw = line.removeprefix("KEYWORDS:").strip()
            keywords = [k.strip() for k in raw.split(",") if k.strip()]
        elif line.startswith("TOPICS:"):
            raw = line.removeprefix("TOPICS:").strip()
            topics = [t.strip() for t in raw.split(",") if t.strip()]

    return {"keywords": keywords, "topics": topics}
