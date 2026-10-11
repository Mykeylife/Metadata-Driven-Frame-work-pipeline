import pytest
import sqlite3

@pytest.fixture
def clean_db_conn():
    """Initializes an in-memory SQLite database seeded with core orchestration tables."""
    conn = sqlite3.connect(":memory:")
    # Allow row-based dictionary scanning
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Create the core metadata configuration table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_metadata (
            step_id INTEGER PRIMARY KEY AUTOINCREMENT,
            step_name TEXT NOT NULL,
            target_table TEXT NOT NULL,
            execution_order INTEGER NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1
        );
    """)

    # 2. CREATE THE MISSING EXECUTION LOGS TABLE (This stops the crash!)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_execution_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            step_name TEXT NOT NULL,
            status TEXT NOT NULL,
            execution_time TEXT NOT NULL,
            error_message TEXT
        );
    """)

    # 3. Create the ingestion table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS staging_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL
        );
    """)

    conn.commit()
    yield conn
    conn.close()
