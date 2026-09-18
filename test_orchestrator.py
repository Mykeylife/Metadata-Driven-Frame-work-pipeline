import sqlite3
import pytest
from adf_src.orchestrator import OrchestratorDB, run_orchestration

@pytest.fixture
def mock_db():
    """Fixture to spin up a clean, isolated in-memory database for every single test execution."""
    # We use an in-memory instance so tests never clash or write permanent files
    db = OrchestratorDB(db_path=":memory:")
    return db

def test_database_initialization_seeds_baseline(mock_db):
    """Verifies that the control table setup functions auto-seed default pipeline metadata."""
    with sqlite3.connect(mock_db.db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Verify the pipeline metadata exists
        cursor.execute("SELECT * FROM pipeline_metadata WHERE pipeline_name = 'sync_student_grades'")
        metadata = cursor.fetchone()
        assert metadata is not None
        assert metadata["target_table"] == "fact_student_grades"
        
        # Verify default execution parameters match our baseline configuration
        cursor.execute("SELECT * FROM pipeline_parameters WHERE pipeline_name = 'sync_student_grades'")
        param = cursor.fetchone()
        assert param is not None
        assert param["parameter_key"] == "batch_size"
        assert param["parameter_value"] == "5000"

def test_get_pipeline_config_returns_none_for_missing_id(mock_db):
    """Ensures looking up an invalid or non-existent configuration returns None gracefully."""
    config = mock_db.get_pipeline_config("invalid_pipeline_name")
    assert config is None

def test_execution_logging_workflow(mock_db):
    """Tracks the transactional states of the logging engine from RUNNING to SUCCESS."""
    pipeline_name = "sync_student_grades"
    
    # 1. Start execution logging tracking
    execution_id = mock_db.start_log(pipeline_name)
    assert execution_id is not None
    assert isinstance(execution_id, str)
    
    with sqlite3.connect(mock_db.db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pipeline_execution_logs WHERE execution_id = ?", (execution_id,))
        log_record = cursor.fetchone()
        assert log_record["status"] == "RUNNING"
    
    # 2. Finalize execution transaction successfully
    mock_db.end_log(execution_id=execution_id, status="SUCCESS", read_count=100, write_count=100)
    
    with sqlite3.connect(mock_db.db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pipeline_execution_logs WHERE execution_id = ?", (execution_id,))
        updated_log = cursor.fetchone()
        assert updated_log["status"] == "SUCCESS"
        assert updated_log["rows_read"] == 100
        assert updated_log["rows_written"] == 100

def test_run_orchestration_happy_path(monkeypatch, mock_db):
    """Verifies full system orchestration runtime passes with an active baseline pipeline profile."""
    # Patch the main OrchestratorDB constructor to redirect to our temporary memory layout during runtime
    monkeypatch.setattr("adf_src.orchestrator.OrchestratorDB", lambda: mock_db)
    
    result = run_orchestration("sync_student_grades")
    assert result == "Success"

def test_run_orchestration_rejected_path(monkeypatch, mock_db):
    """Ensures empty parameters or invalid IDs safely exit out into a Rejected state."""
    monkeypatch.setattr("adf_src.orchestrator.OrchestratorDB", lambda: mock_db)
    
    result = run_orchestration("non_existent_pipeline")
    assert result == "Rejected"
