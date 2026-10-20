"""Unit tests for validating the active TaskCapacityManager batching engine."""

import sqlite3

import pytest

from pipeline.task_manager import TaskCapacityManager


@pytest.fixture
def mock_db_connection():
    """Initializes an in-memory SQLite control database for isolated unit testing."""
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute(
        "CREATE TABLE pipeline_metadata (step_id INTEGER PRIMARY KEY, step_name TEXT UNIQUE, "
        "target_table TEXT, execution_order INTEGER, is_active INTEGER);"
    )
    cursor.execute(
        "CREATE TABLE pipeline_execution_logs (id INTEGER PRIMARY KEY, run_id TEXT, step_name TEXT, "
        "status TEXT, execution_time TEXT, error_message TEXT, data_lineage_hash TEXT, "
        "quality_score REAL, licensing_governance TEXT);"
    )
    conn.commit()
    yield conn
    conn.close()


def test_task_capacity_manager_registration(mock_db_connection):
    """Verifies that individual engineering units track biometric records successfully."""
    manager = TaskCapacityManager(db_connection=mock_db_connection)
    task_id = manager.register_engineering_task("RUN_XYZ", "TEST_STEP", 500)
    assert task_id != "FAILED"
    assert task_id.startswith("TASK_")
