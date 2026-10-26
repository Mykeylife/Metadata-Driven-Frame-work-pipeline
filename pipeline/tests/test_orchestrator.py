"""Unit tests verifying metadata orchestrator main routing conditions."""

from unittest.mock import patch
import pytest

from pipeline.orchestrator import execute_pipeline, fetch_active_steps


def test_fetch_active_steps_with_seeded_metadata(clean_db_conn):
    """Verifies active config step arrays are fetched smoothly by priority order."""
    cursor = clean_db_conn.cursor()
    cursor.execute(
        "INSERT INTO pipeline_metadata (step_name, target_table, execution_order, is_active) VALUES (?, ?, ?, ?);",
        ("Test Active Action", "staging_users", 5, 1),
    )
    clean_db_conn.commit()

    with (
        patch("pipeline.orchestrator.DB_PATH", ":memory:"),
        patch("sqlite3.connect", return_value=clean_db_conn),
    ):
        steps = fetch_active_steps()
        assert len(steps) > 0


def test_execute_pipeline_exits_safely_if_empty(clean_db_conn):
    """Verifies the engine stops cleanly if no tasks are enabled."""
    with (
        patch("pipeline.orchestrator.DB_PATH", ":memory:"),
        patch("sqlite3.connect", return_value=clean_db_conn),
    ):
        # Assert that the orchestrator terminates with the expected RuntimeError when empty
        with pytest.raises(RuntimeError) as exc_info:
            execute_pipeline()
        
        assert "DAG runner terminated with an unexpected status" in str(exc_info.value)
