"""Retrieval module for RAG."""

from .embedder import embed_texts


def retrieve(question: str, vector_store, embedder, top_k: int = 5) -> list[str]:
    """Retrieve relevant text chunks for a question.

    Args:
        question: The question to search for.
        vector_store: VectorStore instance to search.
        embedder: Embedder instance for generating query embedding.
        top_k: Number of results to return.

    Returns:
        List of text chunks (content strings from metadata).
    """
    query_vector = embed_texts([question])[0]
    results = vector_store.search(query_vector, top_k=top_k)

    chunks = []
    for meta in results:
        if "content" in meta:
            chunks.append(meta["content"])
        elif "text" in meta:
            chunks.append(meta["text"])

    return chunks


class Retriever:
    """Retrieve relevant context for queries."""

    def __init__(self, vector_store=None, embedder=None):
        self.vector_store = vector_store
        self.embedder = embedder

    def retrieve(self, query: str, k: int = 5):
        """Retrieve top-k relevant documents."""
        raise NotImplementedError