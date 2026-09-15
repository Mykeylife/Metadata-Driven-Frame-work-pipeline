import pytest
import sqlite3
from orchestrator import MetadataOrchestrator

def test_database_initial_scaffolding():
    """Verifies that the metadata engine structures tables correctly on launch."""
    orchestrator = MetadataOrchestrator(db_path=":memory:")
    
    # Assert core tracking elements are present in the SQLite schema map
    orchestrator.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in orchestrator.cursor.fetchall()]
    
    assert "pipeline_metadata" in tables
    assert "pipeline_parameters" in tables
    assert "pipeline_execution_logs" in tables

def test_pipeline_execution_logging_flow():
    """Tests that active pipelines execute and store logging rows cleanly."""
    orchestrator = MetadataOrchestrator(db_path=":memory:")
    orchestrator.seed_initial_metadata()
    
    # Run the processing logic loop
    orchestrator.execute_active_pipelines()
    
    # Query logs to check status and tracked fields
    orchestrator.cursor.execute("SELECT status, rows_read, rows_written FROM pipeline_execution_logs")
    log_record = orchestrator.cursor.fetchone()
    
    assert log_record is not None
    assert log_record[0] == "SUCCESS"
    assert log_record[1] == 4250  # Verifies processed metrics matching mock logic
    assert log_record[2] == 4250

def test_inactive_pipelines_are_skipped():
    """Ensures the orchestrator skips configuration lines flagged as inactive."""
    orchestrator = MetadataOrchestrator(db_path=":memory:")
    orchestrator.seed_initial_metadata()
    
    # Turn off the pipeline via metadata row update flag
    orchestrator.cursor.execute("UPDATE pipeline_metadata SET is_active = 0 WHERE pipeline_name = 'sync_student_grades'")
    orchestrator.conn.commit()
    
    # Clear logs and execute
    orchestrator.execute_active_pipelines()
    
    orchestrator.cursor.execute("SELECT COUNT(*) FROM pipeline_execution_logs")
    log_count = orchestrator.cursor.fetchone()[0]
    
    assert log_count == 0  # No logs generated because pipeline was safely skipped
