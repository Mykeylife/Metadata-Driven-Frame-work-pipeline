"""Integration tests evaluating end-to-end data pipelines and orchestration paths."""

import sqlite3
from unittest.mock import MagicMock, patch
import pytest
from pipeline.dag_runner import DAGRunner


class IntegrationConnectionPool:
    """Manages transactional environments across unblocked test cycles."""
    
    def __init__(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self._initialize_schema()

    def _initialize_schema(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_metadata (
                step_id INTEGER PRIMARY KEY AUTOINCREMENT,
                step_name TEXT NOT NULL UNIQUE,
                target_table TEXT NOT NULL,
                execution_order INTEGER NOT NULL,
                status TEXT DEFAULT 'PENDING',
                is_active INTEGER DEFAULT 1
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_execution_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                step_name TEXT NOT NULL,
                status TEXT NOT NULL,
                execution_time TEXT NOT NULL,
                error_message TEXT,
                CONSTRAINT unique_run_step UNIQUE (run_id, step_name)
            );
        """)
        cursor.execute("""
            INSERT INTO pipeline_metadata (step_name, target_table, execution_order, is_active)
            VALUES ('Aggregate Analytics Metrics', 'summary_metrics', 10, 1);
        """)
        self.conn.commit()

    def get_connection(self, *args, **kwargs):
        mock_conn = MagicMock(wraps=self.conn)
        mock_conn.close = MagicMock()
        return mock_conn


def test_full_day_runner_pipeline_execution_flow() -> None:
    """Ensures a standard unblocked execution path moves through runner tracking channels cleanly."""
    pool = IntegrationConnectionPool()
    runner = DAGRunner(pipeline_name="End-To-End-Integration-Validation")

    with patch("sqlite3.connect", side_effect=pool.get_connection), \
         patch("pipeline.config.get_db_path", return_value=":memory:"):
        
        runner.run()
        assert runner.status == "SUCCESS"

    pool.conn.close()
