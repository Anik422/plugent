"""Tests for SQLConnector and SchemaParser."""

import pytest
from plugent.db import SQLConnector, SchemaParser, to_prompt_string


class TestSQLConnector:
    """Test SQLConnector functionality."""

    def test_connect_sqlite(self, temp_db):
        """Test connecting to SQLite database."""
        conn = SQLConnector()
        conn.connect(f"sqlite:///{temp_db}")

        tables = conn.get_tables()
        assert len(tables) == 3
        assert "users" in tables
        assert "orders" in tables
        assert "products" in tables

        conn.close()

    def test_get_columns(self, sql_connector):
        """Test fetching columns for a table."""
        columns = sql_connector.get_columns("users")

        assert len(columns) == 4
        col_names = [c["name"] for c in columns]
        assert "id" in col_names
        assert "name" in col_names
        assert "email" in col_names

        # Check primary key
        id_col = next(c for c in columns if c["name"] == "id")
        assert id_col["primary_key"]  # Truthy check for SQLite (1/0 vs True/False)

    def test_get_sample_rows(self, sql_connector):
        """Test fetching sample rows."""
        rows = sql_connector.get_sample_rows("users", n=5)

        assert len(rows) == 2
        assert rows[0]["name"] == "Alice"
        assert rows[1]["name"] == "Bob"

    def test_foreign_keys(self, sql_connector):
        """Test foreign key detection."""
        fks = sql_connector.get_foreign_keys()

        assert "orders" in fks
        assert len(fks["orders"]) == 1
        assert fks["orders"][0]["referred_table"] == "users"

    def test_read_only_mode(self, sql_connector):
        """Test read-only mode enforcement."""
        # SELECT should work
        result = sql_connector.execute_query("SELECT * FROM users")
        assert len(result) == 2

        # INSERT should be blocked (if not read-only by default)
        with pytest.raises(ValueError, match="Only SELECT"):
            sql_connector.execute_query("INSERT INTO users (name) VALUES ('Test')")

    def test_execute_query(self, sql_connector):
        """Test custom query execution."""
        result = sql_connector.execute_query(
            "SELECT name, email FROM users WHERE name = 'Alice'"
        )
        assert len(result) == 1
        assert result[0]["email"] == "alice@example.com"


class TestSchemaParser:
    """Test SchemaParser functionality."""

    def test_parse_schema(self, sql_connector, schema_parser):
        """Test parsing database schema."""
        schema = schema_parser.parse(sql_connector)

        assert len(schema.tables) == 3
        assert schema.business_type == "unknown"

        # Check table names
        table_names = [t.name for t in schema.tables]
        assert "users" in table_names
        assert "orders" in table_names
        assert "products" in table_names

    def test_table_columns(self, sql_connector, schema_parser):
        """Test column parsing."""
        schema = schema_parser.parse(sql_connector)
        users_table = next(t for t in schema.tables if t.name == "users")

        assert len(users_table.columns) == 4
        col_names = [c.name for c in users_table.columns]
        assert "id" in col_names

    def test_sample_rows_parsed(self, sql_connector, schema_parser):
        """Test sample rows are included."""
        schema = schema_parser.parse(sql_connector)
        users_table = next(t for t in schema.tables if t.name == "users")

        assert len(users_table.sample_rows) == 2

    def test_row_counts(self, sql_connector, schema_parser):
        """Test row count extraction."""
        schema = schema_parser.parse(sql_connector)

        counts = schema.row_counts
        assert counts["users"] == 2
        assert counts["orders"] == 1
        assert counts["products"] == 1

    def test_relationships(self, sql_connector, schema_parser):
        """Test foreign key relationships."""
        schema = schema_parser.parse(sql_connector)

        assert len(schema.relationships) == 1
        rel = schema.relationships[0]
        assert rel.source_table == "orders"
        assert rel.target_table == "users"


class TestToPromptString:
    """Test schema to prompt string conversion."""

    def test_format_tables(self, sql_connector, schema_parser):
        """Test table formatting."""
        schema = schema_parser.parse(sql_connector)
        prompt = to_prompt_string(schema)

        assert "## Table: users" in prompt
        assert "### Columns" in prompt
        assert "`id`" in prompt

    def test_format_relationships(self, sql_connector, schema_parser):
        """Test relationship formatting."""
        schema = schema_parser.parse(sql_connector)
        prompt = to_prompt_string(schema)

        assert "## Relationships" in prompt
        assert "orders" in prompt
        assert "users" in prompt

    def test_format_row_counts(self, sql_connector, schema_parser):
        """Test row count display."""
        schema = schema_parser.parse(sql_connector)
        prompt = to_prompt_string(schema)

        assert "Rows:" in prompt