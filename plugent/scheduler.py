"""Task scheduling module for detecting and updating changes."""

from apscheduler.schedulers.background import BackgroundScheduler

from .db_reader import get_row_hashes, read_all_rows
from .embedder import embed_texts


class ChangeScheduler:
    """Schedule periodic checks for database changes."""

    def __init__(self, engine, vector_store, embedder, interval_seconds: int = 60):
        """Initialize the change scheduler.

        Args:
            engine: SQLAlchemy engine connected to database.
            vector_store: VectorStore instance for storing embeddings.
            embedder: Embedder instance for generating embeddings.
            interval_seconds: Interval between change checks (default 60).
        """
        self.engine = engine
        self.vector_store = vector_store
        self.embedder = embedder
        self.interval_seconds = interval_seconds

        self._stored_hashes: dict[str, str] = {}
        self._scheduler: BackgroundScheduler = None

    def start(self):
        """Start the background scheduler."""
        if self._scheduler is not None:
            return

        self._scheduler = BackgroundScheduler()
        self._scheduler.add_job(
            self._check_and_update,
            "interval",
            seconds=self.interval_seconds,
            id="change_check",
        )
        self._scheduler.start()

    def stop(self):
        """Stop the scheduler."""
        if self._scheduler is not None:
            self._scheduler.shutdown()
            self._scheduler = None

    def _check_and_update(self):
        """Check for changes and update vector store.

        Reads current row hashes from DB, compares with stored hashes,
        and updates vector store for new/changed/deleted rows.
        """
        current_hashes = get_row_hashes(self.engine)

        # Find new and changed rows
        new_or_changed_ids = []
        for row_id, row_hash in current_hashes.items():
            if row_id not in self._stored_hashes:
                new_or_changed_ids.append(row_id)
            elif self._stored_hashes[row_id] != row_hash:
                new_or_changed_ids.append(row_id)

        # Find deleted rows
        deleted_ids = set(self._stored_hashes.keys()) - set(current_hashes.keys())

        # Handle deletions
        if deleted_ids:
            self.vector_store.remove_by_ids(list(deleted_ids))

        # Handle new/changed rows
        if new_or_changed_ids:
            rows_to_update = []
            for row in read_all_rows(self.engine):
                if row["row_id"] in new_or_changed_ids:
                    rows_to_update.append(row)

            if rows_to_update:
                contents = [r["content"] for r in rows_to_update]
                vectors = embed_texts(contents)

                for i, row in enumerate(rows_to_update):
                    metadata = {
                        "id": row["row_id"],
                        "table": row["table"],
                        "hash": row["hash"],
                    }
                    self.vector_store.add([vectors[i]], [metadata])

        # Update stored hashes
        self._stored_hashes = current_hashes.copy()


class Scheduler:
    """Schedule and run periodic tasks."""

    def __init__(self):
        pass

    def schedule(self, task, interval: str = None, cron: str = None):
        """Schedule a task."""
        raise NotImplementedError

    def start(self):
        """Start the scheduler."""
        raise NotImplementedError

    def stop(self):
        """Stop the scheduler."""
        raise NotImplementedError