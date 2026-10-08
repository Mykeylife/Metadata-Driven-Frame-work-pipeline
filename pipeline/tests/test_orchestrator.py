import sqlite3
from unittest.mock import MagicMock, patch
import pytest

# Dynamically patch layout pathways before ingestion to ensure zero runtime path collisions
with patch("orchestrator.get_db_path", return_value=":memory:"):
    try:
        from orchestrator import fetch_active_steps, execute_pipeline
    except ImportError:
        from pipeline.orchestrator import fetch_active_steps, execute_pipeline

@pytest.fixture
def orchestrator_db_conn():
    """Provides an isolated in-memory SQLite database setup matching production orchestration metadata schemas."""
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    
    # Replicate the required production control matrix schema exactly
    cursor.execute("""
        CREATE TABLE pipeline_metadata (
            step_id INTEGER PRIMARY KEY AUTOINCREMENT,
            step_name TEXT NOT NULL,
            target_table TEXT NOT NULL,
            execution_order INTEGER NOT NULL,
            is_active INTEGER DEFAULT 1
        );
    """)
    conn.commit()
    yield conn
    conn.close()

def test_fetch_active_steps_with_data(orchestrator_db_conn):
    """Validates that active steps are retrieved correctly and sorted by execution order."""
    cursor = orchestrator_db_conn.cursor()
    cursor.executemany(
        "INSERT INTO pipeline_metadata (step_name, target_table, execution_order, is_active) VALUES (?, ?, ?, ?);",
        [
            ("Extract Users", "staging_users", 20, 1),
            ("Disabled Ingestion", "temp_table", 5, 0),
            ("Process Analytics", "analytics_kpis", 10, 1)
        ]
    )
    orchestrator_db_conn.commit()

    # Intercept runtime connection pools to target our pre-seeded data state
    with patch("orchestrator.get_db_path", return_value=":memory:"), \
         patch("sqlite3.connect", return_value=orchestrator_db_conn):
        
        active_steps = fetch_active_steps()
        
        assert len(active_steps) == 2
        # Verify strict order sorting: "Process Analytics" (Order 10) must run before "Extract Users" (Order 20)
        assert active_steps[0][1] == "Process Analytics"
        assert active_steps[1][1] == "Extract Users"

def test_execute_pipeline_empty_metadata(orchestrator_db_conn):
    """Ensures the orchestration engine exits gracefully if no active rows exist in control maps."""
    with patch("orchestrator.get_db_path", return_value=":memory:"), \
         patch("sqlite3.connect", return_value=orchestrator_db_conn), \
         patch("orchestrator.logger.warning") as mock_warn:
         
        execute_pipeline()
        mock_warn.assert_called_with("No active steps found in control tables. Exiting engine flow safely.")

def test_execute_pipeline_successful_run(orchestrator_db_conn):
    """Verifies complete orchestration path execution handles successful DAGRunner returns cleanly."""
    cursor = orchestrator_db_conn.cursor()
    cursor.execute(
        "INSERT INTO pipeline_metadata (step_name, target_table, execution_order, is_active) VALUES (?, ?, ?, ?);",
        ("Extract Users", "staging_users", 10, 1)
    )
    orchestrator_db_conn.commit()

    # Mock DAGRunner to simulate environment execution footprints without needing live instances
    mock_runner = MagicMock()
    mock_runner.status = "SUCCESS"

    with patch("orchestrator.get_db_path", return_value=":memory:"), \
         patch("sqlite3.connect", return_value=orchestrator_db_conn), \
         patch("orchestrator.DAGRunner", return_value=mock_runner), \
         patch("orchestrator.logger.info") as mock_info:
         
        execute_pipeline()
        # Verify our primary orchestration engine success log tracking statement fired safely
        mock_info.assert_any_call("Metadata-driven orchestrator engine executed all tasks successfully! 🚀")
