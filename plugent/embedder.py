"""Text embedding module."""

import gc
from typing import Optional

import numpy as np
from fastembed import TextEmbedding
from tqdm import tqdm


DEFAULT_EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
_model: Optional[TextEmbedding] = None


def _get_model() -> TextEmbedding:
    global _model

    if _model is None:
        _model = TextEmbedding(DEFAULT_EMBEDDING_MODEL)

    return _model


def embed_texts(texts: list[str], batch_size: int = 100) -> np.ndarray:
    """Generate embeddings for a list of texts.

    Args:
        texts: List of text strings to embed.
        batch_size: Number of texts to embed per batch.

    Returns:
        Numpy array of shape (len(texts), embedding_dim).
    """
    if not texts:
        return np.array([])

    all_vectors = []

    with tqdm(
        total=len(texts),
        desc="Building vector store...",
        unit="rows",
        dynamic_ncols=True,
        bar_format="{desc} {bar} {percentage:3.0f}% | {n_fmt}/{total_fmt} rows | {elapsed}",
    ) as progress_bar:
        for batch_start in range(0, len(texts), batch_size):
            batch_texts = texts[batch_start:batch_start + batch_size]
            batch_vectors = list(_get_model().embed(batch_texts))
            all_vectors.extend(batch_vectors)
            progress_bar.update(len(batch_texts))
            del batch_texts
            del batch_vectors
            gc.collect()

    return np.array(all_vectors)


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