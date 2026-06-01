"""
app/rag/embeddings.py — Converts text into embedding vectors using Gemini.

WHAT is an embedding?
  A list of numbers (a "vector") that encodes the *meaning* of a piece of text.
  Two sentences that mean similar things will have vectors that point in the
  same direction — even if they use different words.

  Example:
    "The dog chased the cat."   → [0.12, -0.45, 0.88, ...]
    "A puppy ran after a kitten." → [0.11, -0.43, 0.85, ...]  ← very close!
    "Stock markets fell today."   → [0.67,  0.22, -0.31, ...]  ← very different

  This lets us find document chunks that are *semantically* relevant to a
  user's question, not just keyword-matched.

COSINE SIMILARITY:
  We measure how close two vectors are using cosine similarity:
    - Score of  1.0  → identical meaning
    - Score of  0.0  → completely unrelated
    - Score of -1.0  → opposite meaning (rare in practice)
"""

import google.generativeai as genai
import numpy as np

from config import EMBEDDING_MODEL, GEMINI_API_KEY

# Configure the Gemini client once at module load time
genai.configure(api_key=GEMINI_API_KEY)


def get_embedding(text: str) -> list[float]:
    """
    Generate an embedding for a document chunk.

    task_type="retrieval_document" tells Google's model that this text is a
    passage to be stored — it optimises the vector for being *found*.
    """
    result = genai.embed_content(
        model=EMBEDDING_MODEL,
        content=text,
        task_type="retrieval_document",
    )
    return result["embedding"]


def get_query_embedding(query: str) -> list[float]:
    """
    Generate an embedding for a user's search query.

    task_type="retrieval_query" optimises the vector for *searching* —
    it's subtly different from the document embedding to improve recall.
    """
    result = genai.embed_content(
        model=EMBEDDING_MODEL,
        content=query,
        task_type="retrieval_query",
    )
    return result["embedding"]


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """
    Return the cosine similarity between two embedding vectors.

    Formula: cos(θ) = (A · B) / (|A| * |B|)
    Using numpy for fast vector math.
    """
    a = np.array(vec1)
    b = np.array(vec2)
    norm = np.linalg.norm(a) * np.linalg.norm(b)
    if norm == 0:
        return 0.0
    return float(np.dot(a, b) / norm)
