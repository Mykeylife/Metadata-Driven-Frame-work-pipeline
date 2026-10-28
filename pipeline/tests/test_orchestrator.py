"""Integration tests verifying full pipeline orchestration routing and safety barriers."""

import sqlite3
from unittest.mock import patch
import pytest

from pipeline.orchestrator import execute_pipeline, fetch_active_steps


@pytest.fixture
def empty_mock_db():
    """Provides a sterile tracking schema lacking active tracking metadata steps."""
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE pipeline_metadata (
            step_id INTEGER PRIMARY KEY AUTOINCREMENT,
            step_name TEXT NOT NULL UNIQUE,
            target_table TEXT NOT NULL,
            execution_order INTEGER NOT NULL,
            is_active INTEGER DEFAULT 1
        );
    """
    )
    conn.commit()
    yield conn
    conn.close()


def test_fetch_active_steps_returns_empty_on_unseeded_database(empty_mock_db):
    """Verifies orchestration lookup managers map clean array structures if no tasks exist."""
    with (
        patch("pipeline.orchestrator.DB_PATH", ":memory:"),
        patch("sqlite3.connect", return_value=empty_mock_db),
    ):
        steps = fetch_active_steps()
        assert list(steps) == []


def test_execute_pipeline_halts_and_raises_on_empty_metadata(empty_mock_db):
    """Validates that empty staging boundaries invoke runtime exception protections successfully."""
    with (
        patch("pipeline.orchestrator.DB_PATH", ":memory:"),
        patch("sqlite3.connect", return_value=empty_mock_db),
    ):
        with pytest.raises(RuntimeError) as exc_info:
            execute_pipeline()

        assert "DAG runner terminated with an unexpected status" in str(
            exc_info.value
        )
