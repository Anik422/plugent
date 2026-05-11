"""ChromaDB-based vector store for plugent."""

import os
from typing import Any

import chromadb
from chromadb.config import Settings

from plugent.llm.base import BaseLLM


class VectorStore:
    """ChromaDB vector store with LLM embeddings."""

    def __init__(self, persist_dir: str = "./chroma_data"):
        """Initialize vector store.

        Args:
            persist_dir: Directory for ChromaDB persistence.
        """
        self.persist_dir = persist_dir
        self._client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False),
        )
        self._llm: BaseLLM | None = None

    def set_llm(self, llm: BaseLLM) -> None:
        """Set LLM for embeddings.

        Args:
            llm: BaseLLM instance with embed() method.
        """
        self._llm = llm

    def add_documents(
        self, docs: list[dict], collection: str
    ) -> None:
        """Add documents to collection.

        Args:
            docs: List of dicts with "id", "text", and optional "metadata".
            collection: Collection name.
        """
        if not self._llm:
            raise RuntimeError("LLM not set. Call set_llm() first.")

        # Get or create collection
        col = self._client.get_or_create_collection(name=collection)

        # Generate embeddings and add documents
        ids = []
        embeddings = []
        texts = []
        metadatas = []

        for doc in docs:
            doc_id = doc.get("id", f"doc_{len(ids)}")
            text = doc.get("text", "")

            if not text:
                continue

            # Generate embedding
            embedding = self._llm.embed(text)

            # Ensure metadata is non-empty (ChromaDB requires this)
            metadata = doc.get("metadata", {})
            if not metadata:
                metadata = {"source": "default"}

            ids.append(doc_id)
            embeddings.append(embedding)
            texts.append(text)
            metadatas.append(metadata)

        # Add to ChromaDB
        if ids:
            col.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
            )

    def search(
        self, query: str, collection: str, n: int = 5
    ) -> list[dict]:
        """Search collection for relevant documents.

        Args:
            query: Search query string.
            collection: Collection name.
            n: Number of results to return.

        Returns:
            List of result dicts with "text", "metadata", "distance".
        """
        if not self._llm:
            raise RuntimeError("LLM not set. Call set_llm() first.")

        col = self._client.get_or_create_collection(name=collection)

        # Generate query embedding
        query_embedding = self._llm.embed(query)

        # Search
        results = col.query(
            query_embeddings=[query_embedding],
            n_results=n,
        )

        # Format results
        output = []
        if results["documents"] and results["documents"][0]:
            for i, text in enumerate(results["documents"][0]):
                output.append({
                    "text": text,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else 0.0,
                })

        return output

    def clear(self, collection: str) -> None:
        """Clear all documents from collection.

        Args:
            collection: Collection name.
        """
        col = self._client.get_or_create_collection(name=collection)
        try:
            self._client.delete_collection(name=collection)
        except Exception:
            pass

    def list_collections(self) -> list[str]:
        """List all collection names.

        Returns:
            List of collection names.
        """
        return [col.name for col in self._client.list_collections()]