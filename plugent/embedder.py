"""Text embedding module."""

from typing import Optional

import numpy as np
from sentence_transformers import SentenceTransformer as STModel


_model: Optional[STModel] = None


def embed_texts(texts: list[str]) -> np.ndarray:
    """Generate embeddings for a list of texts.

    Args:
        texts: List of text strings to embed.

    Returns:
        Numpy array of shape (len(texts), embedding_dim).
    """
    global _model

    if _model is None:
        _model = STModel("all-MiniLM-L6-v2")

    embeddings = _model.encode(texts, convert_to_numpy=True)
    return embeddings


class Embedder:
    """Generate embeddings for text."""

    def __init__(self, model_name: str = None):
        self.model_name = model_name or "all-MiniLM-L6-v2"
        self._model: Optional[STModel] = None

    def embed(self, text: str) -> np.ndarray:
        """Generate embedding for a single text.

        Args:
            text: Text string to embed.

        Returns:
            Numpy array embedding vector.
        """
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: list) -> np.ndarray:
        """Generate embeddings for a batch of texts.

        Args:
            texts: List of text strings to embed.

        Returns:
            Numpy array of embeddings.
        """
        if self._model is None:
            self._model = STModel(self.model_name)

        embeddings = self._model.encode(texts, convert_to_numpy=True)
        return embeddings