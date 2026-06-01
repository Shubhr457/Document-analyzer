"""
app/analysis/ner.py — Named Entity Recognition (NER) using Gemini.

WHAT is NER?
  NER is the task of finding and classifying real-world "named things"
  in text — people, places, organisations, dates, amounts of money, etc.

  Traditional NER uses statistical models trained on annotated corpora
  (spaCy, NLTK, Stanford NER). Using an LLM like Gemini is called "zero-shot NER"
  because we don't need a specially trained model — we just describe what we want.

  Trade-off:
    ✅ LLM NER understands context far better (e.g. "Apple" → company vs fruit)
    ❌ LLM NER is slower and costs API calls; traditional NER runs locally

ENTITY TYPES we extract:
  PERSON       : individual people's names
  ORGANIZATION : companies, institutions, government bodies
  LOCATION     : countries, cities, addresses, geographic features
  DATE         : specific dates, years, time periods
  MONEY        : monetary amounts and currencies
  PRODUCT      : brand names, technologies, software
  EVENT        : named events, conferences, historical events
"""

import google.generativeai as genai

from config import GEMINI_API_KEY, GEMINI_MODEL

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(GEMINI_MODEL)

# The entity categories we want to extract
ENTITY_TYPES = [
    "PERSON",
    "ORGANIZATION",
    "LOCATION",
    "DATE",
    "MONEY",
    "PRODUCT",
    "EVENT",
]


def extract_entities(text: str) -> dict[str, list[str]]:
    """
    Extract all named entities from the document, grouped by type.

    Args:
        text: The document text.

    Returns:
        A dict mapping entity type → list of found entities.
        Empty categories are omitted.

        Example:
        {
          "PERSON":       ["Elon Musk", "Tim Cook"],
          "ORGANIZATION": ["Tesla", "Apple"],
          "LOCATION":     ["California"],
          "DATE":         ["January 2024"],
        }
    """
    if not text.strip():
        return {}

    # 15k chars is plenty for entity extraction — entities are dense near the start
    sample = text[:15_000] if len(text) > 15_000 else text

    # List the categories in the prompt so Gemini knows exactly which labels to use
    category_list = "\n".join(f"  {t}: name1, name2, ..." for t in ENTITY_TYPES)

    prompt = f"""Extract all named entities from the following text.

Respond using ONLY these categories (skip a category if nothing was found):
{category_list}

Text:
{sample}"""

    response = model.generate_content(prompt)
    result_text = response.text.strip()

    # ── Parse the structured response ─────────────────────────────────────────
    entities: dict[str, list[str]] = {}

    for line in result_text.split("\n"):
        line = line.strip()
        for entity_type in ENTITY_TYPES:
            prefix = f"{entity_type}:"
            if line.startswith(prefix):
                raw = line.removeprefix(prefix).strip()
                items = [item.strip() for item in raw.split(",") if item.strip()]
                if items:
                    entities[entity_type] = items
                break

    return entities
