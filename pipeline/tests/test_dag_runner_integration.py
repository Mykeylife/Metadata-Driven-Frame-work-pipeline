"""Integration tests verifying full multi-step end-to-end pipeline runtime paths."""

import os
import sqlite3
from unittest.mock import patch

import pytest

from pipeline.dag_runner import DAGRunner


@pytest.fixture
def integration_db():
    """Sets up a complete integration testing database environment."""
    db_path = "test_integration_control.db"

    # Ensure a stale test database from previous runs doesn't pollute this state
    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Provision schema tables matching operational requirements
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
            metric_name TEXT,
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
            licensing_governance TEXT DEFAULT 'MIT-Data-Asset-v1'
        );
    """
    )

    # Seed an active workflow path into metadata
    cursor.execute(
        "INSERT INTO pipeline_metadata (step_name, target_table, execution_order, is_active) VALUES (?, ?, ?, ?);",
        ("Aggregate Analytics Metrics", "summary_metrics", 10, 1),
    )
    # Seed mock records into tracking tables
    cursor.executemany(
        "INSERT INTO staging_users (id, username) VALUES (?, ?);",
        [(1, "integration_user_a"), (2, "integration_user_b")],
    )

    conn.commit()
    conn.close()

    yield db_path

    # Clean up file side effects after test completion
    if os.path.exists(db_path):
        os.remove(db_path)


def test_full_dag_runner_pipeline_execution_flow(integration_db):
    """Executes a full end-to-end run loop to verify status states and logging entries."""
    runner = DAGRunner(pipeline_name="End-To-End-Integration-Validation")

    # Direct the configuration manager to target our local integration database file path
    with patch("pipeline.config.get_db_path", return_value=integration_db):
        runner.run()

        # 1. Assert runner state transition properties
        assert runner.status == "SUCCESS"

        # 2. Open up the database independently to verify compliance logs
        conn = sqlite3.connect(integration_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM pipeline_execution_logs WHERE step_name = ?;",
            ("Aggregate Analytics Metrics",),
        )
        log_record = cursor.fetchone()

        assert log_record is not None
        assert log_record["status"] == "SUCCESS"
        assert log_record["licensing_governance"] == "MIT-Data-Asset-v1"

        conn.close()
