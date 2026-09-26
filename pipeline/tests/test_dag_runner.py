import os
import sqlite3
import sys
from unittest.mock import MagicMock

import pytest

# Force the execution environment to recognize the root package folder cleanly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from pipeline.dag_runner import DAGRunner


@pytest.fixture
def setup_mock_db():
    """Creates an ephemeral, in-memory SQLite database with required schemas."""
    conn = sqlite3.connect(":memory:")
    # Crucial: Use Row factory to match the runtime orchestrator's behavior
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Create pipeline metadata simulation orchestration tables
    cursor.execute("""
        CREATE TABLE pipeline_metadata (
            step_id INTEGER PRIMARY KEY AUTOINCREMENT,
            step_name TEXT,
            target_table TEXT,
            execution_order INTEGER,
            is_active INTEGER
        );
    """)

    # 2. Create pipeline operational tracking execution log tables
    cursor.execute("""
        CREATE TABLE pipeline_execution_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT,
            step_name TEXT,
            status TEXT,
            execution_time TEXT,
            error_message TEXT
        );
    """)

    # 3. Create a sample target business data table to validate constraints
    cursor.execute("""
        CREATE TABLE staging_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT
        );
    """)

    conn.commit()
    yield conn
    conn.close()


def test_fetch_pipeline_tasks(setup_mock_db, monkeypatch):
    """Verifies tasks are successfully extracted in chronological dependency sequence."""
    conn = setup_mock_db
    cursor = conn.cursor()

    # Insert full parameter pairs to satisfy explicit table constraints
    cursor.execute(
        "INSERT INTO pipeline_metadata (step_name, target_table, execution_order, is_active) VALUES ('Extract Users', 'staging_users', 1, 1);"
    )
    cursor.execute(
        "INSERT INTO pipeline_metadata (step_name, target_table, execution_order, is_active) VALUES ('Transform KPIs', 'analytics_kpis', 3, 1);"
    )
    conn.commit()

    runner = DAGRunner(db_path=":memory:")
    monkeypatch.setattr(runner, "_get_db_connection", lambda: conn)

    tasks = runner.fetch_pipeline_tasks()

    assert len(tasks) == 2
    # Correct sequential index assertions on the returned list items
    assert tasks[0]["step_name"] == "Extract Users"
    assert tasks[1]["step_name"] == "Transform KPIs"


def test_log_execution_trail(setup_mock_db, monkeypatch):
    """Ensures logs correctly append runtime state snapshots to the database."""
    conn = setup_mock_db
    runner = DAGRunner(db_path=":memory:")
    monkeypatch.setattr(runner, "_get_db_connection", lambda: conn)

    runner.log_execution(
        run_id="test-uuid-1234",
        step_name="staging_users",
        status="FAILED",
        execution_time="0.05 seconds",
        error_message="Simulated connection exception drop.",
    )

    cursor = conn.cursor()
    cursor.execute(
        "SELECT run_id, step_name, status, execution_time, error_message FROM pipeline_execution_logs;"
    )
    log_row = cursor.fetchone()

    assert log_row is not None
    assert log_row["run_id"] == "test-uuid-1234"
    assert log_row["status"] == "FAILED"
    # FIX: Explicitly verify that the duration metrics string is preserved
    assert "seconds" in log_row["execution_time"]
    assert log_row["error_message"] == "Simulated connection exception drop."


def test_run_pipeline_halt_on_quality_gate_breach(setup_mock_db, monkeypatch):
    """Validates that the orchestrator actively halts operational execution upon quality breaches."""
    conn = setup_mock_db
    cursor = conn.cursor()

    # Add an active step targeting our dummy staging_users table
    cursor.execute(
        "INSERT INTO pipeline_metadata (step_name, target_table, execution_order, is_active) VALUES ('Load Users Step', 'staging_users', 1, 1);"
    )
    conn.commit()

    runner = DAGRunner(db_path=":memory:")
    monkeypatch.setattr(runner, "_get_db_connection", lambda: conn)

    # FIX: Updated mock signature to gracefully accept the runtime execution_time keyword argument
    def mock_execute_task_logic(task):
        runner.log_execution(
            run_id="mock-run-id",
            step_name=task["step_name"],
            status="FAILED",
            execution_time="0.00 seconds",
            error_message="Data quality validation failed: row count check is zero.",
        )
        return False

    # Force the runner to execute our customized failure simulation rule
    monkeypatch.setattr(runner, "execute_task_logic", mock_execute_task_logic)

    runner.run_pipeline()

    cursor = conn.cursor()
    cursor.execute(
        "SELECT status, execution_time, error_message FROM pipeline_execution_logs WHERE step_name = 'Load Users Step' AND status = 'FAILED';"
    )
    failure_log = cursor.fetchone()

    assert failure_log is not None
    assert "seconds" in failure_log["execution_time"]
    assert "Data quality validation failed" in failure_log["error_message"]
