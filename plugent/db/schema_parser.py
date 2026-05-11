"""Schema parser for plugent."""

from dataclasses import dataclass, field
from typing import Any

from plugent.db.sql_connector import SQLConnector


@dataclass
class ColumnInfo:
    """Column metadata."""

    name: str
    type: str
    nullable: bool
    is_primary: bool = False
    is_foreign: bool = False
    foreign_ref: str | None = None


@dataclass
class TableInfo:
    """Table metadata with sample data."""

    name: str
    columns: list[ColumnInfo] = field(default_factory=list)
    sample_rows: list[dict] = field(default_factory=list)
    description: str = ""


@dataclass
class ForeignKey:
    """Foreign key relationship."""

    source_table: str
    source_columns: list[str]
    target_table: str
    target_columns: list[str]


@dataclass
class SchemaInfo:
    """Complete database schema."""

    tables: list[TableInfo]
    relationships: list[ForeignKey]
    business_type: str = "unknown"
    row_counts: dict[str, int] = field(default_factory=dict)


class SchemaParser:
    """Parse database schema into structured format."""

    def __init__(self, sample_rows_per_table: int = 3):
        """Initialize parser.

        Args:
            sample_rows_per_table: Number of sample rows to fetch per table.
        """
        self.sample_rows_per_table = sample_rows_per_table

    def parse(self, connector: SQLConnector) -> SchemaInfo:
        """Parse database schema.

        Args:
            connector: SQLConnector instance connected to database.

        Returns:
            SchemaInfo with tables, relationships, row counts.
        """
        tables = self._parse_tables(connector)
        relationships = self._parse_relationships(connector)
        row_counts = self._get_row_counts(connector, tables)

        return SchemaInfo(
            tables=tables,
            relationships=relationships,
            row_counts=row_counts,
        )

    def _parse_tables(self, connector: SQLConnector) -> list[TableInfo]:
        """Parse all tables with columns and sample data."""
        table_names = connector.get_tables()
        tables = []

        for table_name in table_names:
            columns = self._parse_columns(connector, table_name)
            try:
                sample_rows = connector.get_sample_rows(
                    table_name, self.sample_rows_per_table
                )
            except Exception:
                sample_rows = []

            tables.append(
                TableInfo(
                    name=table_name,
                    columns=columns,
                    sample_rows=sample_rows,
                )
            )

        return tables

    def _parse_columns(
        self, connector: SQLConnector, table_name: str
    ) -> list[ColumnInfo]:
        """Parse columns for a table."""
        column_data = connector.get_columns(table_name)
        foreign_keys = connector.get_foreign_keys()

        fk_map: dict[str, str] = {}
        if table_name in foreign_keys:
            for fk in foreign_keys[table_name]:
                col = fk["constrained_columns"][0]
                ref = fk["referred_table"]
                fk_map[col] = ref

        columns = []
        for col in column_data:
            columns.append(
                ColumnInfo(
                    name=col["name"],
                    type=col["type"],
                    nullable=col["nullable"],
                    is_primary=col.get("primary_key", False),
                    is_foreign=col["name"] in fk_map,
                    foreign_ref=fk_map.get(col["name"]),
                )
            )

        return columns

    def _parse_relationships(
        self, connector: SQLConnector
    ) -> list[ForeignKey]:
        """Parse all foreign key relationships."""
        fk_data = connector.get_foreign_keys()
        relationships = []

        for table, fks in fk_data.items():
            for fk in fks:
                relationships.append(
                    ForeignKey(
                        source_table=table,
                        source_columns=fk["constrained_columns"],
                        target_table=fk["referred_table"],
                        target_columns=fk["referred_columns"],
                    )
                )

        return relationships

    def _get_row_counts(
        self, connector: SQLConnector, tables: list[TableInfo]
    ) -> dict[str, int]:
        """Get row count for each table."""
        counts = {}
        for table in tables:
            try:
                result = connector.execute_query(
                    f"SELECT COUNT(*) as cnt FROM {table.name}"
                )
                counts[table.name] = result[0]["cnt"] if result else 0
            except Exception:
                counts[table.name] = -1  # Unknown
        return counts


def to_prompt_string(schema: SchemaInfo) -> str:
    """Format schema for LLM prompt.

    Args:
        schema: SchemaInfo to format.

    Returns:
        Formatted string suitable for LLM context.
    """
    lines = ["# Database Schema", ""]

    # Tables
    for table in schema.tables:
        lines.append(f"## Table: {table.name}")
        lines.append(f"**Rows:** {schema.row_counts.get(table.name, '?')}")
        lines.append("")

        # Columns
        lines.append("### Columns")
        for col in table.columns:
            pk = " [PK]" if col.is_primary else ""
            fk = f" [FK → {col.foreign_ref}]" if col.is_foreign else ""
            null = " NULL" if col.nullable else " NOT NULL"
            lines.append(f"- `{col.name}` ({col.type}{null}){pk}{fk}")

        # Sample rows
        if table.sample_rows:
            lines.append("")
            lines.append("### Sample Data")
            for i, row in enumerate(table.sample_rows, 1):
                lines.append(f"Row {i}: {row}")

        lines.append("")

    # Relationships
    if schema.relationships:
        lines.append("## Relationships")
        for rel in schema.relationships:
            src = f"{rel.source_table}.{rel.source_columns[0]}"
            tgt = f"{rel.target_table}.{rel.target_columns[0]}"
            lines.append(f"- {src} → {tgt}")
        lines.append("")

    return "\n".join(lines)