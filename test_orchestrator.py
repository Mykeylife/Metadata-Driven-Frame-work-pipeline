import sqlite3
import pytest
from unittest.mock import MagicMock, patch
from orchestrator import fetch_active_steps, execute_pipeline

@pytest.fixture
def mock_db_setup(tmp_path):
    """Creates a temporary, clean SQLite table layout for isolation testing."""
    db_file = tmp_path / "test_metadata.db"
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE pipeline_metadata (
            step_id INTEGER PRIMARY KEY,
            step_name TEXT NOT NULL,
            target_table TEXT NOT NULL,
            execution_order INTEGER NOT NULL,
            is_active INTEGER DEFAULT 1
        );
    """)
    # Inject deterministic mock step order
    cursor.executemany("""
        INSERT INTO pipeline_metadata VALUES (?, ?, ?, ?, ?);
    """, [
        (1, "Extract Data", "staging_raw", 10, 1),
        (2, "Transform KPIs", "analytics_fact", 20, 1),
        (3, "Disabled Task", "archive_old", 30, 0)
    ])
    conn.commit()
    conn.close()
    return str(db_file)

@patch("orchestrator.DB_PATH")
def test_fetch_active_steps_filtering(mock_db_path, mock_db_setup):
    """Verifies fetch_active_steps sorts items by order and filters out inactive rows."""
    with patch("orchestrator.get_db_path", return_value=mock_db_setup):
        # Force re-evaluation of the path context inside the test thread
        with patch("orchestrator.DB_PATH", mock_db_setup):
            steps = fetch_active_steps()
            
            # Assert only active records were fetched
            assert len(steps) == 2
            # Assert proper execution priority sort tracking
            assert steps[0][1] == "Extract Data"
            assert steps[1][1] == "Transform KPIs"

@patch("orchestrator.fetch_active_steps")
@patch("orchestrator.DAGRunner")
def test_execute_pipeline_success_flow(MockDAGRunner, mock_fetch):
    """Asserts orchestrator triggers DAG execution cleanly when active rows exist."""
    mock_fetch.return_value = [(1, "Extract Data", "staging_raw", 10)]
    
    mock_runner_instance = MagicMock()
    mock_runner_instance.status = "SUCCESS"
    MockDAGRunner.return_value = mock_runner_instance
    
    # Run orchestration execution gate loop
    execute_pipeline()
    
    mock_runner_instance.run.assert_called_once()

@patch("orchestrator.fetch_active_steps")
@patch("orchestrator.DAGRunner")
def test_execute_pipeline_empty_graceful_exit(MockDAGRunner, mock_fetch):
    """Ensures orchestrator safely exits without spinning up a runner if no steps match."""
    mock_fetch.return_value = []
    
    execute_pipeline()
    
    MockDAGRunner.assert_not_called()
