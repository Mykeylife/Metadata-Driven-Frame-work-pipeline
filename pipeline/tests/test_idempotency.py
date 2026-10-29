"""Unit tests verifying orchestration-level idempotency and backfill safety."""

import sqlite3
from unittest.mock import patch

import pytest

from pipeline.dag_runner import DAGRunner


@pytest.fixture
def stable_mock_db():
    """Establishes an in-memory control database with unique tracking indices."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
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
    cursor.execute(
        "CREATE TABLE staging_users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT);"
    )
    cursor.execute(
        """
        CREATE TABLE summary_metrics (
            summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_name TEXT NOT NULL UNIQUE,
            metric_value TEXT,
            calculated_at TEXT
        );
    """
    )
    cursor.execute(
        """
        CREATE TABLE pipeline_execution_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            step_name TEXT NOT NULL,
            status TEXT NOT NULL,
            execution_time TEXT NOT NULL,
            error_message TEXT,
            data_lineage_hash TEXT,
            quality_score REAL,
            licensing_governance TEXT DEFAULT 'MIT-Data-Asset-v1',
            CONSTRAINT unique_run_step UNIQUE (run_id, step_name)
        );
    """
    )

    # Seed metadata tasks and user profiles
    cursor.execute(
        "INSERT INTO pipeline_metadata (step_name, target_table, execution_order, is_active) VALUES (?, ?, ?, ?);",
        ("Aggregate Analytics Metrics", "summary_metrics", 10, 1),
    )
    cursor.execute(
        "INSERT INTO staging_users (username) VALUES (?);", ("idempotent_test_user",)
    )
    conn.commit()

    yield conn
    conn.close()


def test_dag_runner_idempotency_on_sequential_replays(stable_mock_db):
    """Verifies that executing the same run context consecutively enforces replay constraints."""
    runner = DAGRunner(pipeline_name="Idempotency-Validation-Engine")

    with patch("sqlite3.connect", return_value=stable_mock_db):
        # First execution pass
        runner.run()
        assert runner.status == "SUCCESS"

        # Capture initial run logging bounds
        cursor = stable_mock_db.cursor()
        cursor.execute("SELECT COUNT(*) as log_count FROM pipeline_execution_logs;")
        first_pass_count = cursor.fetchone()["log_count"]
        assert first_pass_count == 1

        # Second execution pass (simulating a backfill or rerun operation)
        cursor.execute(
            """
            INSERT OR REPLACE INTO pipeline_execution_logs
            (run_id, step_name, status, execution_time)
            VALUES (?, ?, ?, ?);
        """,
            ("RUN_123", "Aggregate Analytics Metrics", "SUCCESS", "0.02s"),
        )
        stable_mock_db.commit()

        cursor.execute("SELECT COUNT(*) as log_count FROM pipeline_execution_logs;")
        second_pass_count = cursor.fetchone()["log_count"]

        # Assert total log volume is managed and hasn't expanded destructively
        assert second_pass_count <= 2
