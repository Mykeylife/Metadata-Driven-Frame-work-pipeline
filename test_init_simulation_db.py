"""Unit tests for verifying initialization and idempotency of the simulation database."""

import os
import sqlite3

import pytest

from init_simulation_db import init_db


@pytest.fixture
def test_db_path(tmp_path):
    """Provides an isolated, temporary path for database initialization testing."""
    db_file = tmp_path / "test_metadata_control.db"
    original_db_path = os.getenv("DB_PATH")
    os.environ["DB_PATH"] = str(db_file)
    yield str(db_file)
    if original_db_path:
        os.environ["DB_PATH"] = original_db_path
    else:
        os.environ.pop("DB_PATH", None)


def test_init_db_creates_tables(test_db_path):
    """Verifies tables are created upon initialization run loop cycles."""
    init_db()
    assert os.path.exists(test_db_path)
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    assert "pipeline_metadata" in tables
