"""
app/analysis/sentiment.py — Determines the emotional tone of a document.

WHAT is sentiment analysis?
  Classifying whether text expresses a Positive, Negative, Neutral, or Mixed
  tone. Traditional NLP used word lists ("great" = positive, "terrible" = negative).
  LLMs like Gemini understand nuance and context — sarcasm, hedging language,
  mixed reviews — far better than keyword-based approaches.

USE CASES:
  - Business: analyse customer feedback documents
  - Research: gauge the tone of news articles or academic papers
  - HR: understand employee survey responses

OUTPUT:
  We extract four fields from Gemini's response:
    - sentiment    : Positive / Negative / Neutral / Mixed
    - confidence   : High / Medium / Low
    - explanation  : one or two sentence rationale
    - key_emotions : list of detected emotions (joy, frustration, hope, etc.)
"""

import google.generativeai as genai

from config import GEMINI_API_KEY, GEMINI_MODEL

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(GEMINI_MODEL)


def analyze_sentiment(text: str) -> dict:
    """
    Analyse the overall sentiment and emotional tone of the document.

    Args:
        text: The document text to analyse.

    Returns:
        {
          "sentiment":   "Positive" | "Negative" | "Neutral" | "Mixed",
          "confidence":  "High" | "Medium" | "Low",
          "explanation": "...",
          "key_emotions": ["joy", "frustration", ...]
        }
    """
    if not text.strip():
        return {
            "sentiment": "Neutral",
            "confidence": "Low",
            "explanation": "No text provided.",
            "key_emotions": [],
        }

    # For sentiment we only need a representative sample, not the full text
    sample = text[:10_000] if len(text) > 10_000 else text

    prompt = f"""Analyze the overall sentiment and emotional tone of the following text.

Respond in EXACTLY this format (no extra lines):
SENTIMENT: [Positive/Negative/Neutral/Mixed]
CONFIDENCE: [High/Medium/Low]
EXPLANATION: [One or two sentences explaining why]
KEY_EMOTIONS: [comma-separated list of detected emotions]

Text:
{sample}"""

    response = model.generate_content(prompt)
    result_text = response.text.strip()

    # ── Parse structured response ─────────────────────────────────────────────
    result: dict = {
        "sentiment": "Neutral",
        "confidence": "Medium",
        "explanation": "",
        "key_emotions": [],
    }

    for line in result_text.split("\n"):
        line = line.strip()
        if line.startswith("SENTIMENT:"):
            result["sentiment"] = line.removeprefix("SENTIMENT:").strip()
        elif line.startswith("CONFIDENCE:"):
            result["confidence"] = line.removeprefix("CONFIDENCE:").strip()
        elif line.startswith("EXPLANATION:"):
            result["explanation"] = line.removeprefix("EXPLANATION:").strip()
        elif line.startswith("KEY_EMOTIONS:"):
            raw = line.removeprefix("KEY_EMOTIONS:").strip()
            result["key_emotions"] = [e.strip() for e in raw.split(",") if e.strip()]

    return result
