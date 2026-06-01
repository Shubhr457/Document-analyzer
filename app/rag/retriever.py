"""
app/rag/retriever.py — Stores document chunks + embeddings, retrieves relevant ones.

This is the "R" in RAG (Retrieval-Augmented Generation).

Full RAG pipeline:
  1. [Index]    Split document → embed each chunk → store in memory
  2. [Retrieve] Embed the user's question → find the most similar chunks
  3. [Generate] Pass those chunks as context to Gemini → get a grounded answer

We keep the vector store in-memory (a plain Python list) to keep things simple
and dependency-free. For production you'd use ChromaDB, Pinecone, or pgvector.
"""

from app.rag.chunker import chunk_text
from app.rag.embeddings import cosine_similarity, get_embedding, get_query_embedding
from config import TOP_K_CHUNKS


class DocumentRetriever:
    """
    A simple in-memory vector store for one document at a time.

    Attributes:
        chunks     : the raw text of each chunk
        embeddings : the embedding vector corresponding to each chunk
    """

    def __init__(self) -> None:
        self.chunks: list[str] = []
        self.embeddings: list[list[float]] = []

    def index_document(self, text: str) -> int:
        """
        Chunk the document and generate + store an embedding for each chunk.

        This is called once per document load. It can take a few seconds
        because we make one Gemini API call per chunk.

        Returns the number of chunks created.
        """
        # Reset any previously indexed document
        self.chunks = []
        self.embeddings = []

        chunks = chunk_text(text)

        for chunk in chunks:
            embedding = get_embedding(chunk)
            self.chunks.append(chunk)
            self.embeddings.append(embedding)

        return len(self.chunks)

    def retrieve(self, query: str, top_k: int = TOP_K_CHUNKS) -> list[dict]:
        """
        Find the `top_k` chunks most relevant to `query`.

        Steps:
          1. Embed the query
          2. Compute cosine similarity against every stored chunk embedding
          3. Return the top_k chunks sorted by score (highest first)

        Returns a list of dicts: [{"chunk": str, "score": float}, ...]
        """
        if not self.chunks:
            return []

        query_embedding = get_query_embedding(query)

        # Score every chunk
        scores = [
            cosine_similarity(query_embedding, chunk_emb)
            for chunk_emb in self.embeddings
        ]

        # Pick the indices of the top_k highest scores
        top_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True,
        )[:top_k]

        return [
            {"chunk": self.chunks[i], "score": round(scores[i], 4)} for i in top_indices
        ]

    @property
    def is_indexed(self) -> bool:
        """True if a document has been indexed and is ready for Q&A."""
        return len(self.chunks) > 0
