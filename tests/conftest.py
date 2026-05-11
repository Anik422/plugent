"""Pytest fixtures for plugent tests."""

import pytest
import tempfile
import os
import sqlite3
from unittest.mock import MagicMock

from plugent.llm.base import BaseLLM, Message
from plugent.db import SQLConnector, SchemaParser
from plugent.core import Skill, SkillBuilder, BusinessContext, BusinessDetector
from plugent.knowledge import VectorStore
from plugent.core import ReactAgent


@pytest.fixture
def temp_db():
    """Create a temporary SQLite database with sample data."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    conn = sqlite3.connect(path)
    cursor = conn.cursor()

    # Create tables
    cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            product TEXT,
            amount REAL,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT,
            price REAL
        )
    """)

    # Insert sample data
    cursor.execute("INSERT INTO users (name, email) VALUES ('Alice', 'alice@example.com')")
    cursor.execute("INSERT INTO users (name, email) VALUES ('Bob', 'bob@example.com')")
    cursor.execute("INSERT INTO orders (user_id, product, amount, status) VALUES (1, 'Widget', 99.99, 'completed')")
    cursor.execute("INSERT INTO products (name, category, price) VALUES ('Gadget', 'Electronics', 49.99)")

    conn.commit()
    conn.close()

    yield path

    os.unlink(path)


@pytest.fixture
def sql_connector(temp_db):
    """Create SQLConnector connected to temp DB."""
    conn = SQLConnector()
    conn.connect(f"sqlite:///{temp_db}")
    yield conn
    conn.close()


@pytest.fixture
def schema_parser():
    """Create SchemaParser instance."""
    return SchemaParser()


@pytest.fixture
def mock_llm():
    """Create a mock LLM that returns predetermined responses."""
    llm = MagicMock(spec=BaseLLM)

    # Default response
    llm.chat.return_value = "Test response"
    llm.embed.return_value = [0.1] * 384

    def set_response(response):
        llm.chat.return_value = response

    llm.set_response = set_response

    return llm


@pytest.fixture
def mock_business_context():
    """Create a mock BusinessContext."""
    return BusinessContext(
        business_type="ecommerce",
        key_entities=[
            {"table": "users", "description": "Customer accounts"},
            {"table": "orders", "description": "Customer purchases"},
        ],
        suggested_skills=["order_lookup", "user_lookup"],
        primary_language="en",
        confidence=0.9,
    )


@pytest.fixture
def sample_skills():
    """Create sample Skill objects."""
    skills = []

    def execute_order_lookup(order_id: str) -> str:
        return f"Order {order_id}: pending"

    skill = Skill(
        name="order_lookup",
        description="Look up order by ID",
        parameters=[{"name": "order_id", "type": "string", "description": "Order ID"}],
    )
    skill._execute_fn = execute_order_lookup
    skills.append(skill)

    def execute_user_lookup(user_id: str) -> str:
        return f"User {user_id}: Alice"

    skill = Skill(
        name="user_lookup",
        description="Look up user by ID",
        parameters=[{"name": "user_id", "type": "string", "description": "User ID"}],
    )
    skill._execute_fn = execute_user_lookup
    skills.append(skill)

    return skills


@pytest.fixture
def vector_store(tmp_path):
    """Create VectorStore with temp directory."""
    store = VectorStore(persist_dir=str(tmp_path / "chroma"))
    return store


@pytest.fixture
def company_config():
    """Sample company config."""
    return {
        "name": "Test Corp",
        "description": "Test company",
        "domain": "ecommerce",
    }