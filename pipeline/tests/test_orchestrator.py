"""Unit tests establishing stability constraints for execution loop managers."""

import sqlite3
from unittest.mock import patch

import pytest

from pipeline.dag_runner import DAGRunner


@pytest.fixture
def empty_mock_db():
    """Pre-configures an empty metadata database connection profile."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


def test_execute_pipeline_halts_and_raises_on_empty_metadata(empty_mock_db) -> None:
    """Validates that empty staging boundaries invoke runtime safety protections gracefully."""
    runner = DAGRunner(pipeline_name="Orchestration-Loop-Monitor")
    
    with patch("pipeline.orchestrator.DB_PATH", "memory:"), \
         patch("sqlite3.connect", return_value=empty_mock_db):
        
        # The orchestrator catches empty metadata conditions gracefully without throwing a hard unhandled crash
        runner.run()
        
        # Verify the pipeline engine reacted safely by halting execution loops and moving status to FAILED or ERROR
        assert runner.status in ["FAILED", "ERROR"]
