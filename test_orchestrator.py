import sqlite3
import pytest
from orchestrator import PipelineOrchestrator, run_pipeline
from models import PipelineRun, PipelineExecutionError


@pytest.fixture
def memory_db_conn():
    """Provides a clean, isolated in-memory SQLite database setup for orchestrator tests."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Explicitly build the modern table structures required by the model validations
    cursor.execute("""
        CREATE TABLE pipeline_metadata (
            step_id INTEGER PRIMARY KEY AUTOINCREMENT,
            step_name TEXT NOT NULL UNIQUE,
            target_table TEXT NOT NULL,
            execution_order INTEGER NOT NULL,
            is_active INTEGER DEFAULT 1
        );
    """)
    cursor.execute("""
        CREATE TABLE pipeline_execution_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            step_name TEXT NOT NULL,
            status TEXT NOT NULL,
            execution_time TEXT NOT NULL,
            error_message TEXT
        );
    """)
    # Pre-seed business schemas to satisfy deep execution loops inside DAGRunner dependencies
    cursor.execute("CREATE TABLE IF NOT EXISTS staging_users (id INTEGER PRIMARY KEY, username TEXT);")
    cursor.execute("CREATE TABLE IF NOT EXISTS analytics_kpis (kpi_id INTEGER PRIMARY KEY, username TEXT, username_length INTEGER, processed_at TEXT);")
    cursor.execute("CREATE TABLE IF NOT EXISTS summary_metrics (summary_id INTEGER PRIMARY KEY, metric_name TEXT, metric_value TEXT, calculated_at TEXT);")
    
    conn.commit()
    yield conn
    conn.close()


def test_orchestrator_execution(memory_db_conn):
    """Verifies that the orchestrator successfully updates pipeline states and logs footprints."""
    cursor = memory_db_conn.cursor()
    # Seed an active metadata task step row mapping tracking configuration
    cursor.execute("""
        INSERT INTO pipeline_metadata (step_name, target_table, execution_order, is_active)
        VALUES ('Extract Users', 'staging_users', 10, 1);
    """)
    memory_db_conn.commit()

    orchestrator = PipelineOrchestrator(db_conn=memory_db_conn)

    # Run the pipeline test
    result = orchestrator.run_pipeline("run_test_001", "Main-Pipeline-Orchestration")
    
    # Verify both data structures are accurately populated
    assert isinstance(result, PipelineRun)
    assert result.status == "SUCCESS"
    assert result.run_id == "run_test_001"
    
    # Assert database state validation logic passes properly
    orchestrator.validate_execution_logs("run_test_001")


def test_inactive_pipeline_throws_error(memory_db_conn):
    """Ensures that our custom validation exception triggers correctly if no tasks are active."""
    orchestrator = PipelineOrchestrator(db_conn=memory_db_conn)

    # Assert that running on an unseeded/inactive configuration triggers our exception barrier
    with pytest.raises(PipelineExecutionError):
        orchestrator.run_pipeline("run_test_002", "Disabled-Pipeline")


def test_module_level_run_pipeline_helper(memory_db_conn):
    """Validates that the simple module-level runner function helper acts identically."""
    cursor = memory_db_conn.cursor()
    cursor.execute("""
        INSERT INTO pipeline_metadata (step_name, target_table, execution_order, is_active)
        VALUES ('Extract Users', 'staging_users', 10, 1);
    """)
    memory_db_conn.commit()

    result = run_pipeline(run_id="run_test_003", pipeline_name="Helper-Pipeline", db_conn=memory_db_conn)
    
    assert result.status == "SUCCESS"
    assert result.run_id == "run_test_003"
