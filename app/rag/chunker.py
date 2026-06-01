"""
app/rag/chunker.py — Splits a long document into smaller overlapping chunks.

WHY do we chunk?
  LLMs have a "context window" — a limit on how many tokens (words) they can
  process at once. A 100-page PDF is way too long to send all at once.
  Instead, we split it into small pieces, embed each piece, and only send
  the *relevant* pieces to the LLM when answering a question.

WHY overlap?
  If chunk 1 ends at sentence A and chunk 2 starts at sentence B, any
  information spanning both sentences would be split and lost. Overlap
  ensures every sentence appears in at least one complete chunk.
"""

from config import CHUNK_OVERLAP, CHUNK_SIZE


def chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[str]:
    """
    Split `text` into overlapping chunks of approximately `chunk_size` chars.

    The function also tries to break at a sentence boundary (". " or "\\n")
    in the last 20% of each chunk, so chunks don't end mid-sentence.

    Returns a list of non-empty string chunks.
    """
    if not text.strip():
        return []

    chunks: list[str] = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        chunk = text[start:end]

        # ── Smart boundary detection ──────────────────────────────────────
        # If we haven't reached the end of the document, try to break at a
        # sentence or paragraph boundary inside the last 20% of the chunk.
        if end < len(text):
            search_from = int(chunk_size * 0.8)  # search only the tail

            # Prefer breaking after a period+space (sentence end)
            break_point = chunk.rfind(". ", search_from)

            # Fall back to a newline (paragraph end)
            if break_point == -1:
                break_point = chunk.rfind("\n", search_from)

            # If we found a good break point, trim the chunk there
            if break_point != -1:
                end = start + break_point + 1
                chunk = text[start:end]

        chunks.append(chunk.strip())

        # Move the window forward, but step back by `overlap` characters
        # so the next chunk begins slightly before this one ended.
        start = end - overlap

    # Filter out any empty strings that might have snuck in
    return [c for c in chunks if c]
