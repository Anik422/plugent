"""Tests for plugent core module."""

import pytest
from unittest.mock import MagicMock, patch

from plugent import Plugent


class TestPlugent:
    """Test suite for Plugent class."""

    def test_plugent_init(self):
        """Test that Plugent class initializes without error."""
        plugent = Plugent(
            groq_api_key="test_key",
            postgres_url="postgresql://localhost/testdb",
            vector_store_path="./test_store",
            schedule_interval=30,
        )
        assert plugent.groq_api_key == "test_key"
        assert plugent.postgres_url == "postgresql://localhost/testdb"
        assert plugent.vector_store_path == "./test_store"
        assert plugent.schedule_interval == 30

    @patch("plugent.core.create_engine")
    @patch("plugent.core.read_all_rows")
    @patch("plugent.core.embed_texts")
    @patch("plugent.core.VectorStore")
    @patch("plugent.core.ChangeScheduler")
    def test_start_calls_db_and_embedder(
        self, mock_scheduler, mock_vector_store, mock_embed, mock_read, mock_engine
    ):
        """Test that start() calls db_reader and embedder functions."""
        mock_read.return_value = [
            {"row_id": 1, "table": "users", "content": "name: alice", "hash": "abc123"},
            {"row_id": 2, "table": "users", "content": "name: bob", "hash": "def456"},
        ]
        mock_embed.return_value = [[0.1, 0.2], [0.3, 0.4]]
        mock_vs_instance = MagicMock()
        mock_vector_store.return_value = mock_vs_instance

        plugent = Plugent(
            groq_api_key="test_key",
            postgres_url="postgresql://localhost/testdb",
        )
        plugent.start()

        mock_read.assert_called_once()
        mock_embed.assert_called_once()
        mock_vs_instance.add.assert_called()
        mock_vs_instance.save.assert_called()
        mock_scheduler.assert_called_once()

    @patch("plugent.core.retrieve")
    @patch("plugent.core.get_answer")
    def test_ask_returns_string(self, mock_answer, mock_retrieve):
        """Test that ask() returns a string."""
        mock_retrieve.return_value = ["context chunk 1", "context chunk 2"]
        mock_answer.return_value = "This is the answer."

        plugent = Plugent(
            groq_api_key="test_key",
            postgres_url="postgresql://localhost/testdb",
        )
        plugent.vector_store = MagicMock()
        plugent.groq_api_key = "test_key"

        result = plugent.ask("What is the user's name?")

        assert isinstance(result, str)
        mock_retrieve.assert_called_once()
        mock_answer.assert_called_once()

    @patch("plugent.core.ChangeScheduler")
    def test_stop_stops_scheduler(self, mock_scheduler):
        """Test that stop() stops the scheduler."""
        mock_scheduler_instance = MagicMock()
        mock_scheduler.return_value = mock_scheduler_instance

        plugent = Plugent(
            groq_api_key="test_key",
            postgres_url="postgresql://localhost/testdb",
        )
        plugent.scheduler = mock_scheduler_instance

        plugent.stop()

        mock_scheduler_instance.stop.assert_called_once()