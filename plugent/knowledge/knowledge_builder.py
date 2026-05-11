"""Knowledge builder for plugent - convert data to embeddings."""

import os
from typing import Any

from plugent.db.sql_connector import SQLConnector
from plugent.db.schema_parser import SchemaInfo
from plugent.knowledge.vector_store import VectorStore


class KnowledgeBuilder:
    """Build knowledge base from database and files."""

    def __init__(self, vector_store: VectorStore):
        """Initialize knowledge builder.

        Args:
            vector_store: VectorStore instance.
        """
        self.vector_store = vector_store

    def from_database(
        self,
        connector: SQLConnector,
        collection: str = "db_knowledge",
    ) -> int:
        """Read tables, convert to sentences, embed and store.

        Args:
            connector: SQLConnector connected to database.
            collection: Target collection name.

        Returns:
            Number of documents added.
        """
        tables = connector.get_tables()
        docs = []

        for table in tables:
            # Get sample rows
            try:
                rows = connector.get_sample_rows(table, n=10)
                if not rows:
                    continue

                # Get columns for better formatting
                columns = connector.get_columns(table)
                col_names = [c["name"] for c in columns]

                # Convert each row to readable sentence
                for i, row in enumerate(rows):
                    sentence = self._row_to_sentence(table, row, col_names)
                    docs.append({
                        "id": f"{table}_{i}",
                        "text": sentence,
                        "metadata": {"source": table, "type": "db_row"},
                    })
            except Exception:
                continue

        # Add to vector store
        if docs:
            self.vector_store.add_documents(docs, collection)

        return len(docs)

    def from_file(
        self,
        file_path: str,
        collection: str = "file_knowledge",
        chunk_size: int = 1000,
    ) -> int:
        """Load plain text or markdown file as knowledge.

        Args:
            file_path: Path to .txt or .md file.
            collection: Target collection name.
            chunk_size: Max characters per chunk.

        Returns:
            Number of chunks added.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        if ext not in [".txt", ".md"]:
            raise ValueError(f"Unsupported file type: {ext}")

        # Read file
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Chunk content
        chunks = self._chunk_text(content, chunk_size)

        # Create documents
        docs = []
        filename = os.path.basename(file_path)
        for i, chunk in enumerate(chunks):
            docs.append({
                "id": f"{filename}_{i}",
                "text": chunk.strip(),
                "metadata": {"source": filename, "type": "file"},
            })

        # Add to vector store
        if docs:
            self.vector_store.add_documents(docs, collection)

        return len(docs)

    def from_directory(
        self,
        dir_path: str,
        collection: str = "file_knowledge",
        extensions: list[str] = None,
    ) -> int:
        """Load all supported files from directory.

        Args:
            dir_path: Directory path.
            collection: Target collection name.
            extensions: List of file extensions to include.

        Returns:
            Total number of chunks added.
        """
        if extensions is None:
            extensions = [".txt", ".md"]

        total = 0
        for root, _, files in os.walk(dir_path):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in extensions:
                    file_path = os.path.join(root, file)
                    try:
                        count = self.from_file(file_path, collection)
                        total += count
                    except Exception:
                        continue

        return total

    def _row_to_sentence(
        self, table: str, row: dict, columns: list[str]
    ) -> str:
        """Convert database row to readable sentence."""
        parts = []

        for col in columns:
            if col in row and row[col] is not None:
                value = row[col]

                # Format value based on type
                if isinstance(value, str):
                    # Wrap string values in quotes
                    parts.append(f"{col} is '{value}'")
                elif isinstance(value, (int, float)):
                    parts.append(f"{col} is {value}")
                elif isinstance(value, bool):
                    parts.append(f"{col} is {value}")
                else:
                    parts.append(f"{col} is {value}")

        if not parts:
            return f"Row in {table}"

        return f"In {table}, " + ", ".join(parts) + "."

    def _chunk_text(self, text: str, chunk_size: int) -> list[str]:
        """Split text into chunks."""
        chunks = []
        lines = text.split("\n")
        current = []

        for line in lines:
            current.append(line)
            if sum(len(l) for l in current) > chunk_size:
                chunks.append("\n".join(current))
                current = []

        if current:
            chunks.append("\n".join(current))

        return chunks