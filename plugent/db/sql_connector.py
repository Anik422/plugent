"""SQLAlchemy-based SQL connector for plugent."""

from typing import Any
from sqlalchemy import (
    create_engine,
    inspect,
    text,
    MetaData,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session


class SQLConnector:
    """SQLAlchemy connector with read-only mode enforcement."""

    SUPPORTED_DIALECTS = ["postgresql", "mysql", "sqlite", "mssql"]

    def __init__(self, read_only: bool = True):
        """Initialize connector.

        Args:
            read_only: If True, enforces read-only mode (rollback after each query).
        """
        self._engine: Engine | None = None
        self._session: Session | None = None
        self._inspector: inspect | None = None
        self._read_only = read_only
        self._metadata = MetaData()

    def connect(self, db_url: str) -> None:
        """Connect to database.

        Args:
            db_url: SQLAlchemy connection URL (postgresql://, mysql://, sqlite://, mssql://).

        Raises:
            ValueError: If dialect not supported.
        """
        dialect = db_url.split("://")[0].split("+")[0].lower()
        if dialect not in self.SUPPORTED_DIALECTS:
            raise ValueError(
                f"Unsupported dialect: {dialect}. Supported: {self.SUPPORTED_DIALECTS}"
            )

        self._engine = create_engine(db_url, pool_pre_ping=True)
        self._session = sessionmaker(bind=self._engine)()
        self._inspector = inspect(self._engine)

    def get_tables(self) -> list[str]:
        """Get list of all tables.

        Returns:
            List of table names.
        """
        if not self._inspector:
            raise RuntimeError("Not connected. Call connect() first.")
        return self._inspector.get_table_names()

    def get_columns(self, table: str) -> list[dict]:
        """Get column metadata for a table.

        Args:
            table: Table name.

        Returns:
            List of column info dicts with keys: name, type, nullable, default, primary_key.
        """
        if not self._inspector:
            raise RuntimeError("Not connected. Call connect() first.")

        columns = self._inspector.get_columns(table)
        return [
            {
                "name": col["name"],
                "type": str(col["type"]),
                "nullable": col["nullable"],
                "default": str(col.get("default")) if col.get("default") else None,
                "primary_key": col.get("primary_key", False),
            }
            for col in columns
        ]

    def get_sample_rows(self, table: str, n: int = 5) -> list[dict]:
        """Get sample rows from table.

        Args:
            table: Table name.
            n: Number of rows to fetch.

        Returns:
            List of row dicts.
        """
        if not self._session:
            raise RuntimeError("Not connected. Call connect() first.")

        query = text(f"SELECT * FROM {table} LIMIT :limit")
        result = self._execute_readonly(query, {"limit": n})
        return [dict(row._mapping) for row in result]

    def execute_query(self, sql: str) -> list[dict]:
        """Execute a SELECT query and return results.

        Args:
            sql: SQL SELECT query.

        Returns:
            List of result row dicts.
        """
        if not self._session:
            raise RuntimeError("Not connected. Call connect() first.")

        # Only allow SELECT queries in read-only mode
        if self._read_only and not sql.strip().upper().startswith("SELECT"):
            raise ValueError("Only SELECT queries allowed in read-only mode")

        query = text(sql)
        result = self._execute_readonly(query)
        return [dict(row._mapping) for row in result]

    def get_foreign_keys(self) -> dict[str, list[dict]]:
        """Get all foreign keys in the database.

        Returns:
            Dict mapping table name to list of FK info dicts.
        """
        if not self._inspector:
            raise RuntimeError("Not connected. Call connect() first.")

        foreign_keys = {}
        for table in self._inspector.get_table_names():
            fks = self._inspector.get_foreign_keys(table)
            if fks:
                foreign_keys[table] = [
                    {
                        "constrained_columns": fk["constrained_columns"],
                        "referred_table": fk["referred_table"],
                        "referred_columns": fk["referred_columns"],
                    }
                    for fk in fks
                ]
        return foreign_keys

    def _execute_readonly(self, query, params: dict | None = None) -> Any:
        """Execute query in read-only mode with rollback.

        Args:
            query: SQLAlchemy text query.
            params: Query parameters.

        Returns:
            Query result.
        """
        if self._read_only and self._session:
            try:
                result = self._session.execute(query, params or {})
                self._session.rollback()
                return result
            except Exception as e:
                self._session.rollback()
                raise e
        else:
            return self._session.execute(query, params or {})

    def close(self) -> None:
        """Close connection."""
        if self._session:
            self._session.close()
        if self._engine:
            self._engine.dispose()

    def __enter__(self) -> "SQLConnector":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()