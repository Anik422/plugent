"""Text embedding module."""

from typing import Optional

import numpy as np
from fastembed import TextEmbedding


DEFAULT_EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
_model: Optional[TextEmbedding] = None


def _get_model() -> TextEmbedding:
    global _model

    if _model is None:
        _model = TextEmbedding(DEFAULT_EMBEDDING_MODEL)

    return _model


def embed_texts(texts: list[str]) -> np.ndarray:
    """Generate embeddings for a list of texts.

    Args:
        texts: List of text strings to embed.

    Returns:
        Numpy array of shape (len(texts), embedding_dim).
    """
    vectors = list(_get_model().embed(texts))
    return np.array(vectors)


class Embedder:
    """Generate embeddings for text."""

    def __init__(self, model_name: str = None):
        self.model_name = model_name or DEFAULT_EMBEDDING_MODEL
        self._model: Optional[TextEmbedding] = None

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
            self._model = TextEmbedding(self.model_name)

        vectors = list(self._model.embed(texts))
        return np.array(vectors)