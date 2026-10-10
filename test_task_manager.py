"""Unit tests for validating the active TaskCapacityManager batching engine."""

import pytest
import sqlite3
from pipeline.task_manager import TaskCapacityManager  # Correct, verified class name

@pytest.fixture
def mock_db_connection():
    """Initializes an in-memory SQLite control database for isolated unit testing."""
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    # Create the control table required by TaskCapacityManager
    cursor.execute("""
        CREATE TABLE pipeline_metadata (
            step_id INTEGER PRIMARY KEY AUTOINCREMENT,
            step_name TEXT NOT NULL UNIQUE,
            target_table TEXT NOT NULL,
            execution_order INTEGER NOT NULL,
            is_active INTEGER DEFAULT 1
        )
    """)
    # Seed mock records for processing loops
    cursor.executemany("""
        INSERT INTO pipeline_metadata (step_name, target_table, execution_order, is_active)
        VALUES (?, ?, ?, ?)
    """, [
        ("staging_users", "staging_users", 1, 1),
        ("analytics_kpis", "analytics_kpis", 2, 1),
        ("disabled_step", "disabled_table", 3, 0)
    ])
    conn.commit()
    yield conn
    conn.close()

def test_task_capacity_manager_registration(mock_db_connection):
    """Asserts that TaskCapacityManager extracts only active operational pipeline steps."""
    manager = TaskCapacityManager(db_connection=mock_db_connection)
    active_steps = manager.get_active_steps()
    
    # Validation constraints: step 1 and step 2 must load; disabled_step must be dropped
    assert len(active_steps) == 2
    assert "staging_users" in active_steps
    assert "analytics_kpis" in active_steps
    assert "disabled_step" not in active_steps

def test_task_capacity_manager_execution_order(mock_db_connection):
    """Verifies that the orchestrator loop processes targets sequentially by order index."""
    manager = TaskCapacityManager(db_connection=mock_db_connection)
    ordered_steps = manager.get_ordered_execution_steps()
    
    assert ordered_steps[0] == "staging_users"   # execution_order = 1
    assert ordered_steps[1] == "analytics_kpis"   # execution_order = 2
