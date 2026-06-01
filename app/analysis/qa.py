"""
app/analysis/qa.py — Question & Answer over a document using RAG.

HOW RAG WORKS (step by step):

  Step 1 — Indexing (done once when the document is loaded):
    The document is split into chunks → each chunk is converted to an embedding
    vector → stored in the DocumentRetriever.

  Step 2 — Retrieval (done for every question):
    The user's question is converted to an embedding vector.
    We compare that vector to all stored chunk vectors using cosine similarity.
    The top-K most similar chunks are returned.

  Step 3 — Augmented Generation:
    Those chunks are inserted into a prompt as "context".
    Gemini reads the context and answers the question based on it.
    By grounding the answer in retrieved text, we prevent hallucination.

WHY is this better than just asking Gemini the question directly?
  Without context: Gemini answers from its training data (may be wrong/outdated).
  With RAG:        Gemini answers from *your specific document* (grounded, accurate).
"""

import google.generativeai as genai

from app.rag.retriever import DocumentRetriever
from config import GEMINI_API_KEY, GEMINI_MODEL

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(GEMINI_MODEL)


def answer_question(question: str, retriever: DocumentRetriever) -> dict:
    """
    Answer a user's question using RAG over the indexed document.

    Args:
        question:  The user's question as a plain string.
        retriever: A DocumentRetriever that has already been indexed.

    Returns:
        {
          "answer":  "The answer text...",
          "sources": [{"chunk": "...", "score": 0.87}, ...]
        }

    The "sources" list shows which chunks were used, so the user can
    verify the answer against the original document.
    """
    if not retriever.is_indexed:
        return {
            "answer": "No document has been indexed yet. Please load a document first.",
            "sources": [],
        }

    # ── Step 1: Retrieve the most relevant chunks ─────────────────────────────
    relevant_chunks = retriever.retrieve(question)

    # ── Step 2: Build the context string ─────────────────────────────────────
    # We join the chunks with a separator so Gemini knows where one ends and
    # the next begins. More context = better answers (up to the token limit).
    context = "\n\n---\n\n".join(chunk["chunk"] for chunk in relevant_chunks)

    # ── Step 3: Build the RAG prompt ──────────────────────────────────────────
    # The key instruction: "answer based ONLY on the provided context".
    # This is called "grounding" — it prevents the model from making things up.
    prompt = f"""You are a helpful assistant that answers questions about a document.
Answer the question using ONLY the information in the context below.
If the answer is not present in the context, say: "I couldn't find this information in the document."

Context from document:
{context}

Question: {question}

Answer:"""

    response = model.generate_content(prompt)

    return {
        "answer": response.text.strip(),
        "sources": relevant_chunks,
    }
