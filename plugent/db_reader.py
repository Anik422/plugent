"""Database reader module."""

import hashlib

from sqlalchemy import MetaData, Table, inspect, select


def read_all_rows(engine, max_rows=None):
    """Read rows from all tables in the database.

    Args:
        engine: SQLAlchemy engine connected to PostgreSQL.
        max_rows: Optional per-table row limit.

    Yields:
        Dicts with keys: table, row_id, content, hash.
    """
    inspector = inspect(engine)
    metadata = MetaData()
    metadata.reflect(bind=engine)

    for table_name in inspector.get_table_names():
        table = Table(table_name, metadata, autoload_with=engine)
        query = select(table)
        if max_rows is not None:
            query = query.limit(max_rows)

        with engine.connect() as conn:
            for row in conn.execute(query):
                row_dict = dict(row._mapping)
                row_id = row_dict.get("id") or row_dict.get("pk")
                content = ", ".join(f"{k}: {v}" for k, v in row_dict.items())
                content_hash = hashlib.md5(content.encode()).hexdigest()
                yield {
                    "table": table_name,
                    "row_id": row_id,
                    "content": content,
                    "hash": content_hash,
                }


def get_row_hashes(engine) -> dict[str, str]:
    """Get unique_id to hash mapping for all rows.

    Args:
        engine: SQLAlchemy engine connected to PostgreSQL.

    Returns:
        Dict mapping unique_id to hash.
    """
    inspector = inspect(engine)
    metadata = MetaData()
    metadata.reflect(bind=engine)

    hashes = {}

    for table_name in inspector.get_table_names():
        table = Table(table_name, metadata, autoload_with=engine)
        pk_cols = inspector.get_pk_constraint(table_name)["constrained_columns"]

        with engine.connect() as conn:
            for row in conn.execute(table.select()):
                row_dict = dict(row._mapping)
                unique_id = f"{table_name}:{row_dict.get(pk_cols[0]) if pk_cols else row_dict.get('id')}"
                content = ", ".join(f"{k}: {v}" for k, v in row_dict.items())
                content_hash = hashlib.md5(content.encode()).hexdigest()
                hashes[unique_id] = content_hash

    return hashes


class DBReader:
    """Read data from databases."""

    def __init__(self, connection_string: str = None):
        self.connection_string = connection_string

    def read(self, query: str):
        """Execute a read query."""
        raise NotImplementedError

    def get_schema(self):
        """Get database schema."""
        raise NotImplementedError