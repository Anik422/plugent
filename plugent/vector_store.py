"""Vector storage module using FAISS."""

import os
import pickle
from typing import Any

import faiss
import numpy as np


class VectorStore:
    """Store and query vector embeddings using FAISS."""

    def __init__(self, dimension: int = None):
        self.dimension = dimension
        self._index: faiss.Index = None
        self._metadata: list[dict] = []

    def add(self, vectors: list, metadata_list: list[dict] = None):
        """Add vectors with metadata to the store.

        Args:
            vectors: List of vectors (2D numpy array or list of lists).
            metadata_list: List of metadata dicts corresponding to each vector.
        """
        if vectors is None or len(vectors) == 0:
            return

        vectors_arr = np.array(vectors, dtype=np.float32)
        if vectors_arr.ndim == 1:
            vectors_arr = vectors_arr.reshape(1, -1)

        if self._index is None:
            dim = vectors_arr.shape[1]
            self._index = faiss.IndexFlatL2(dim)
            self.dimension = dim

        self._index.add(vectors_arr)

        if metadata_list is None:
            metadata_list = [{}] * len(vectors)
        self._metadata.extend(metadata_list)

    def search(self, query_vector: list, top_k: int = 5) -> list[dict]:
        """Search for most similar vectors.

        Args:
            query_vector: Query vector (list or 1D array).
            top_k: Number of results to return.

        Returns:
            List of metadata dicts for top-k results.
        """
        if self._index is None:
            return []

        query_arr = np.array(query_vector, dtype=np.float32).reshape(1, -1)
        distances, indices = self._index.search(query_arr, min(top_k, self._index.ntotal))

        results = []
        for idx in indices[0]:
            if idx >= 0 and idx < len(self._metadata):
                results.append(self._metadata[idx])
        return results

    def save(self, path: str):
        """Save index and metadata to disk.

        Args:
            path: Base path for saving (will create .index and .meta files).
        """
        if self._index is None:
            raise ValueError("No index to save")

        faiss.write_index(self._index, f"{path}.index")
        with open(f"{path}.meta", "wb") as f:
            pickle.dump(self._metadata, f)

    def load(self, path: str):
        """Load index and metadata from disk.

        Args:
            path: Base path for loading (expects .index and .meta files).
        """
        self._index = faiss.read_index(f"{path}.index")
        with open(f"{path}.meta", "rb") as f:
            self._metadata = pickle.load(f)
        self.dimension = self._index.d

    def remove_by_ids(self, id_list: list):
        """Remove entries by ID.

        Args:
            id_list: List of IDs to remove (metadata must contain 'id' field).
        """
        ids_to_remove = set(id_list)
        new_metadata = []
        new_vectors = []

        for i, meta in enumerate(self._metadata):
            if meta.get("id") not in ids_to_remove:
                new_metadata.append(meta)
                if self._index is not None:
                    vec = self._index.reconstruct(i)
                    new_vectors.append(vec)

        self._metadata = new_metadata

        if new_vectors:
            dim = self._index.d
            self._index = faiss.IndexFlatL2(dim)
            self._index.add(np.array(new_vectors, dtype=np.float32))
        else:
            self._index = None