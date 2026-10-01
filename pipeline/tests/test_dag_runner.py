import pytest
import sqlite3
from unittest.mock import patch, MagicMock

# Pre-emptively mock configuration targets before importing to protect local workspaces
with patch("pipeline.config.get_db_path", return_value=":memory:"):
    try:
        from pipeline.dag_runner import DAGRunner
    except ImportError:
        # Fallback to local import depending on path collection context
        from dag_runner import DAGRunner

@pytest.fixture
def mock_db_connection():
    """Provides a pristine, isolated in-memory metadata context for DAG runner execution tests."""
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    
    # Establish standard metadata tracking controls matching your ecosystem layout
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_metadata (
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

def test_dag_runner_initialization():
    """Verifies that the runner initializes parameters correctly."""
    runner = DAGRunner(pipeline_name="Ingestion-Engine-Validation")
    assert runner.pipeline_name == "Ingestion-Engine-Validation"
    assert runner.status == "PENDING"

def test_dag_runner_successful_execution_loop(mock_db_connection):
    """Ensures the DAG execution engine iterates through active pipeline steps successfully."""
    cursor = mock_db_connection.cursor()
    cursor.execute(
        "INSERT INTO pipeline_metadata (step_name, target_table, execution_order, is_active) VALUES (?, ?, ?, ?);",
        ("Extract Logs", "staging_logs", 10, 1)
    )
    mock_db_connection.commit()

    runner = DAGRunner(pipeline_name="Ingestion-Engine-Validation")
    
    with patch("sqlite3.connect", return_value=mock_db_connection), \
         patch("logging.Logger.info") as mock_logger:
        
        # Execute runner lifecycle block
        runner.run()
        
        # Verify status transitions cleanly to success footprint
        assert runner.status == "SUCCESS"
        mock_logger.assert_any_call("DAG step execution completed cleanly.")

def test_dag_runner_handles_empty_steps(mock_db_connection):
    """Validates that the runner transitions to an optimized safety state if no tasks match."""
    runner = DAGRunner(pipeline_name="Ingestion-Engine-Validation")
    
    with patch("sqlite3.connect", return_value=mock_db_connection), \
         patch("logging.Logger.warning") as mock_logger:
        
        runner.run()
        
        assert runner.status == "SKIPPED"
        mock_logger.assert_any_call("No operational steps registered for execution context.")

def test_dag_runner_catches_ingestion_exceptions(mock_db_connection):
    """Ensures that exceptions inside individual pipeline steps fail the loop immediately."""
    cursor = mock_db_connection.cursor()
    cursor.execute(
        "INSERT INTO pipeline_metadata (step_name, target_table, execution_order, is_active) VALUES (?, ?, ?, ?);",
        ("Failing Step", "corrupted_table", 10, 1)
    )
    mock_db_connection.commit()

    runner = DAGRunner(pipeline_name="Ingestion-Engine-Validation")
    
    # Force a runtime environment break inside the data loop execution layer
    with patch("sqlite3.connect", return_value=mock_db_connection), \
         patch("sqlite3.Cursor.fetchall", side_effect=sqlite3.OperationalError("Database locks encountered.")):
         
        with pytest.raises(sqlite3.OperationalError):
            runner.run()
            
        assert runner.status == "FAILED"
