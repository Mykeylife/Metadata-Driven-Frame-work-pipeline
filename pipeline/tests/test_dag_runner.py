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
            username TEXT NOT NULL
        );
    """)

    # 4. Create target analytics KPI storage schema to match production
    cursor.execute("""
        CREATE TABLE analytics_kpis (
            kpi_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            username_length INTEGER NOT NULL,
            processed_at TEXT NOT NULL
        );
    """)

    conn.commit()
    yield conn
    conn.close()


def test_fetch_pipeline_tasks(setup_mock_db, monkeypatch):
    """Verifies tasks are successfully extracted in chronological dependency sequence."""
    conn = setup_mock_db
    cursor = conn.cursor()

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
    assert "seconds" in log_row["execution_time"]
    assert log_row["error_message"] == "Simulated connection exception drop."


def test_real_kpi_transformation_loop(setup_mock_db, monkeypatch):
    """Validates that the pipeline accurately processes metrics calculations on business records."""
    conn = setup_mock_db
    cursor = conn.cursor()

    # 1. Populate source data table with concrete text records to test transformation math
    cursor.execute("INSERT INTO staging_users (username) VALUES ('Olanrewaju');")
    cursor.execute("INSERT INTO staging_users (username) VALUES ('Myke');")
    conn.commit()

    runner = DAGRunner(db_path=":memory:")
    monkeypatch.setattr(runner, "_get_db_connection", lambda: conn)

    # 2. Fire live calculation processing layer for target schema
    task_definition = {"target_table": "analytics_kpis", "step_name": "Transform Metric KPIs"}
    success = runner.execute_task_logic(task_definition)

    assert success is True

    # 3. Validate string measurement calculations are natively accurate
    cursor.execute("SELECT username, username_length FROM analytics_kpis ORDER BY username_length DESC;")
    records = cursor.fetchall()

    assert len(records) == 2
    assert records[0]["username"] == "Olanrewaju"
    assert records[0]["username_length"] == 10  # Len of 'Olanrewaju'
    assert records[1]["username"] == "Myke"
    assert records[1]["username_length"] == 4   # Len of 'Myke'
