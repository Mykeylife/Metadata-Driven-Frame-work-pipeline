import sqlite3
import pytest
from unittest.mock import patch
from pipeline.orchestrator import PipelineOrchestrator  # Adjust import based on your exact orchestrator location

@pytest.fixture
def temp_orchestration_db(tmp_path):
    """Sets up a mock database environment specifically for checking execution state mutations."""
    db_path = tmp_path / "test_orchestrator_control.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_metadata (
            task_id TEXT PRIMARY KEY,
            task_name TEXT,
            status TEXT
        )
    """)
    cursor.execute("INSERT INTO pipeline_metadata VALUES ('critical_task', 'Process Analytics', 'PENDING')")
    conn.commit()
    conn.close()
    return str(db_path)

def test_orchestrator_failure_branch_transitions(temp_orchestration_db):
    """Asserts that when an execution node encounters an unhandled runtime error, the orchestrator updates state to FAILED."""
    db_path = temp_orchestration_db
    orchestrator = PipelineOrchestrator(db_path=db_path)
    
    # Mocking the low-level processing task to explicitly raise an error during execution
    with patch("pipeline.orchestrator.PipelineOrchestrator._execute_node") as mock_execute:
        mock_execute.side_effect = RuntimeError("Simulated processing subsystem failure")
        
        # Execute orchestrator pipeline loop; verify it returns False or logs gracefully rather than crashing completely
        execution_success = orchestrator.execute_pipeline(task_id="critical_task")
        assert execution_success is False, "Orchestrator reported success despite a critical task failure."
        
    # Query database state to ensure the security/safety guards moved the task status to FAILED
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM pipeline_metadata WHERE task_id='critical_task'")
    resulting_status = cursor.fetchone()[0]
    conn.close()
    
    assert resulting_status == "FAILED", f"Expected task status to transition to 'FAILED', found '{resulting_status}' instead."
