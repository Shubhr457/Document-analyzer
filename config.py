"""
config.py — Central configuration for the Document Analyzer.

All settings live here so you never have to hunt through the codebase
to change a model name, chunk size, or anything else. Think of this
as the "control panel" of the entire project.
"""

import os

from dotenv import load_dotenv

# load_dotenv() reads the .env file and puts the values into the
# environment, so os.getenv() can find them. This keeps secrets out of code.
load_dotenv()

# ── Gemini API ────────────────────────────────────────────────────────────────

GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

# gemini-1.5-flash is fast, capable, and free-tier friendly
GEMINI_MODEL: str = "gemini-1.5-flash"

# Google's best text-embedding model — produces 768-dimensional vectors
EMBEDDING_MODEL: str = "models/text-embedding-004"

# ── RAG (Retrieval-Augmented Generation) ─────────────────────────────────────

# Number of characters in each chunk when we split a document
CHUNK_SIZE: int = 1000

# Overlap between consecutive chunks.
# Example: chunk 1 ends at char 1000, chunk 2 starts at char 800.
# This prevents losing context that sits right on a boundary.
CHUNK_OVERLAP: int = 200

# How many chunks to retrieve and pass to Gemini when answering a question
TOP_K_CHUNKS: int = 5
