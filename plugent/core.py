"""Main core module for plugent."""


def _missing_dependency(name: str):
    def _raise(*args, **kwargs):
        raise ImportError(
            f"{name} is unavailable because an optional plugent dependency is missing."
        )

    return _raise


try:
    from sqlalchemy import create_engine
except ImportError:  # pragma: no cover - exercised only when dependency is absent
    create_engine = _missing_dependency("sqlalchemy.create_engine")

try:
    from .db_reader import read_all_rows
except ImportError:  # pragma: no cover - exercised only when dependency is absent
    read_all_rows = _missing_dependency("plugent.db_reader.read_all_rows")

try:
    from .embedder import embed_texts
except ImportError:  # pragma: no cover - exercised only when dependency is absent
    embed_texts = _missing_dependency("plugent.embedder.embed_texts")

try:
    from .scheduler import ChangeScheduler
except ImportError:  # pragma: no cover - exercised only when dependency is absent
    class ChangeScheduler:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            raise ImportError(
                "plugent.scheduler.ChangeScheduler is unavailable because an optional plugent dependency is missing."
            )

try:
    from .retriever import retrieve
except ImportError:  # pragma: no cover - exercised only when dependency is absent
    retrieve = _missing_dependency("plugent.retriever.retrieve")

try:
    from .responder import get_answer
except ImportError:  # pragma: no cover - exercised only when dependency is absent
    get_answer = _missing_dependency("plugent.responder.get_answer")

try:
    from .vector_store import VectorStore
except ImportError:  # pragma: no cover - exercised only when dependency is absent
    class VectorStore:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            raise ImportError(
                "plugent.vector_store.VectorStore is unavailable because an optional plugent dependency is missing."
            )


class Plugent:
    """Main plugent class for RAG with scheduled updates."""

    def __init__(
        self,
        groq_api_key: str,
        postgres_url: str,
        vector_store_path: str = "./plugent_store",
        schedule_interval: int = 60,
    ):
        """Initialize Plugent.

        Args:
            groq_api_key: Groq API key for LLM responses.
            postgres_url: PostgreSQL connection URL.
            vector_store_path: Path to save/load vector store.
            schedule_interval: Seconds between DB change checks.
        """
        self.groq_api_key = groq_api_key
        self.postgres_url = postgres_url
        self.vector_store_path = vector_store_path
        self.schedule_interval = schedule_interval

        self.engine = None
        self.vector_store = None
        self.scheduler = None

    def start(self):
        """Start plugent: connect to DB, build and save vector store, start scheduler."""
        self.engine = create_engine(self.postgres_url)

        rows = read_all_rows(self.engine)
        if not rows:
            self.vector_store = VectorStore()
            return

        contents = [r["content"] for r in rows]
        vectors = embed_texts(contents)

        self.vector_store = VectorStore()
        metadata_list = [
            {
                "id": r["row_id"],
                "table": r["table"],
                "hash": r["hash"],
                "content": r["content"],
            }
            for r in rows
        ]
        self.vector_store.add(vectors, metadata_list)
        self.vector_store.save(self.vector_store_path)

        self.scheduler = ChangeScheduler(
            engine=self.engine,
            vector_store=self.vector_store,
            embedder=None,
            interval_seconds=self.schedule_interval,
        )
        self.scheduler.start()

    def ask(self, question: str) -> str:
        """Ask a question and get an answer.

        Args:
            question: User question.

        Returns:
            Answer string from LLM.
        """
        try:
            from . import embedder as emb_module
        except ImportError:
            emb_module = None

        context_chunks = retrieve(
            question=question,
            vector_store=self.vector_store,
            embedder=emb_module,
            top_k=5,
        )

        if not context_chunks:
            return "I don't have information about that."

        answer = get_answer(
            question=question,
            context_chunks=context_chunks,
            groq_api_key=self.groq_api_key,
        )
        return answer

    def stop(self):
        """Stop the scheduler."""
        if self.scheduler is not None:
            self.scheduler.stop()


class Core:
    """Main core class for the plugent framework."""

    def __init__(self):
        pass

    def run(self):
        """Run the core logic."""
        raise NotImplementedError