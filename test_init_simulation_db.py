import os
import sqlite3
import pytest
from init_simulation_db import init_db


@pytest.fixture
def test_db_path(tmp_path):
    """Provides an isolated, temporary path for database initialization testing."""
    db_file = os.path.join(tmp_path, "test_simulation_temp.db")
    yield db_file
    # Cleanup happens automatically through tmp_path teardown closures


def test_database_initialization_and_schema_completeness(test_db_path):
    """Verifies that all 5 critical staging, metadata, and analytical tables are created and seeded."""
    # 1. Run initialization for the first time to create the schema infrastructure
    init_db(db_path=test_db_path)
    
    # Verify the physical database file asset was generated properly
    assert os.path.exists(test_db_path) is True

    # Establish localized validation connection
    conn = sqlite3.connect(test_db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Query master catalogs to verify existence of all 5 target schemas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row["name"] for row in cursor.fetchall()]
    
    assert "pipeline_metadata" in tables
    assert "pipeline_execution_logs" in tables
    assert "staging_users" in tables
    assert "analytics_kpis" in tables
    assert "summary_metrics" in tables
    
    # Assert that the logging table features the new biometric monitoring fields
    cursor.execute("PRAGMA table_info(pipeline_execution_logs);")
    columns = {row["name"]: row["type"] for row in cursor.fetchall()}
    
    assert "peak_memory_kb" in columns
    assert "cpu_time_seconds" in columns
    assert columns["peak_memory_kb"] == "INTEGER"
    assert columns["cpu_time_seconds"] == "REAL"
    
    # Assert that core sequential workflow steps were accurately seeded
    cursor.execute("SELECT step_name, target_table FROM pipeline_metadata ORDER BY execution_order ASC;")
    seeded_tasks = cursor.fetchall()
    
    assert len(seeded_tasks) == 3
    assert seeded_tasks[0]["target_table"] == "staging_users"
    assert seeded_tasks[1]["target_table"] == "analytics_kpis"
    assert seeded_tasks[2]["target_table"] == "summary_metrics"
    
    # Confirm initial staging user profiles were correctly loaded
    cursor.execute("SELECT COUNT(*) as user_count FROM staging_users;")
    assert cursor.fetchone()["user_count"] == 3
    
    conn.close()


def test_database_initialization_idempotency(test_db_path):
    """Ensures that re-running the provisioning logic is idempotent and does not break or duplicate data."""
    # Run the initialization twice consecutively
    init_db(db_path=test_db_path)
    
    try:
        init_db(db_path=test_db_path)
        idempotency_passed = True
    except sqlite3.Error as e:
        idempotency_passed = False
        print(f"Idempotency validation failed with database crash barrier: {e}")
        
    assert idempotency_passed is True, "Database initialization logic failed on consecutive execution passes."

    # Validate that re-running did not duplicate seeded metadata rows or staging users
    conn = sqlite3.connect(test_db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as task_count FROM pipeline_metadata;")
    assert cursor.fetchone()["task_count"] == 3
    
    cursor.execute("SELECT COUNT(*) as user_count FROM staging_users;")
    assert cursor.fetchone()["user_count"] == 3
    
    conn.close()
