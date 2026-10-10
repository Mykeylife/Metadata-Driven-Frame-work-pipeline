"""Database abstraction layer for metadata pipeline transactions."""

import sqlite3
from typing import List, Tuple

def get_active_steps(cursor: sqlite3.Cursor) -> List[Tuple[str, str, int]]:
    """Retrieves all active pipeline stages ordered by their execution sequence."""
    cursor.execute("""
        SELECT step_name, target_table, execution_order 
        FROM pipeline_metadata 
        WHERE is_active = 1 
        ORDER BY execution_order ASC
    """)
    return cursor.fetchall()

def log_pipeline_execution(cursor: sqlite3.Cursor, run_id: str, step_name: str, status: str, execution_time: float, error_message: str = None) -> None:
    """Inserts precise microsecond execution telemetry metrics into audit logs."""
    cursor.execute("""
        INSERT INTO pipeline_execution_logs (run_id, step_name, status, execution_time, error_message)
        VALUES (?, ?, ?, ?, ?)
    """, (run_id, step_name, status, str(execution_time), error_message))
