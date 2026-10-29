"""Integration tests evaluating end-to-end data pipelines and orchestration paths."""

import sqlite3
from unittest.mock import patch

import pytest

from pipeline.dag_runner import DAGRunner


@pytest.fixture
def base_integration_db():
    """Provides a structural in-memory configuration layout for integration evaluations."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Establish necessary tables to clear boot schema validation constraints
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS pipeline_metadata (
            step_id INTEGER PRIMARY KEY AUTOINCREMENT,
            step_name TEXT NOT NULL UNIQUE,
            target_table TEXT NOT NULL,
            execution_order INTEGER NOT NULL,
            status TEXT DEFAULT 'PENDING',
            is_active INTEGER DEFAULT 1
        );
    """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS pipeline_execution_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            step_name TEXT NOT NULL,
            status TEXT NOT NULL,
            execution_time TEXT NOT NULL,
            error_message TEXT,
            CONSTRAINT unique_run_step UNIQUE (run_id, step_name)
        );
    """
    )
    
    # Seed a valid active step so the runner has an execution task to process
    cursor.execute(
        """
        INSERT INTO pipeline_metadata (step_name, target_table, execution_order, is_active)
        VALUES (?, ?, ?, ?);
        """,
        ("Simulated Data Process Step", "staging_users", 10, 1)
    )
    conn.commit()
    yield conn
    conn.close()


def test_full_day_runner_pipeline_execution_flow(base_integration_db) -> None:
    """Ensures a standard unblocked execution path moves through runner tracking channels cleanly."""
    runner = DAGRunner(pipeline_name="End-To-End-Integration-Validation")
    
    # Mock both configuration path and connection to ensure the setup database is queried
    with patch("sqlite3.connect", return_value=base_integration_db), \
         patch("pipeline.config.get_db_path", return_value="test_integration_control.db"):
        runner.run()
        assert runner.status == "SUCCESS"
