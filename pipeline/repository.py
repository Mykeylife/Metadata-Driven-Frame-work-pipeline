"""Database abstraction layer for pipeline control matrix operations."""

import sqlite3
from typing import Any


def fetch_active_metadata_steps(cursor: sqlite3.Cursor) -> list[dict[str, Any]]:
    """Fetches valid operational workflow stages sorted by sequence priority."""
    cursor.execute("""
        SELECT step_id, step_name, target_table, execution_order 
        FROM pipeline_metadata 
        WHERE is_active = 1
        ORDER BY execution_order ASC;
    """)
    return [dict(row) for row in cursor.fetchall()]


def check_table_row_count(cursor: sqlite3.Cursor, table_name: str) -> int:
    """Safely checks row volume counts for data quality assertion gates."""
    cursor.execute(f"SELECT COUNT(*) as cnt FROM {table_name};")
    row = cursor.fetchone()
    return row["cnt"] if row else 0


def fetch_staging_usernames(cursor: sqlite3.Cursor) -> list[sqlite3.Row]:
    """Extracts raw username arrays out of staging datasets."""
    cursor.execute("SELECT username FROM staging_users;")
    return cursor.fetchall()


def insert_summary_metric(cursor: sqlite3.Cursor, name: str, value: str) -> None:
    """Commits compiled summary metric records into reporting blocks."""
    cursor.execute("""
        INSERT INTO summary_metrics (metric_name, metric_value, calculated_at)
        VALUES (?, ?, datetime('now'));
    """, (name, value))


def insert_analytics_kpi(cursor: sqlite3.Cursor, username: str, length: int) -> None:
    """Writes mapped analytical identity calculations out to metric stores."""
    cursor.execute("""
        INSERT INTO analytics_kpis (username, username_length, processed_at)
        VALUES (?, ?, datetime('now'));
    """, (username, length))


def log_pipeline_telemetry(
    cursor: sqlite3.Cursor, 
    run_id: str, 
    step_name: str, 
    status: str, 
    error_message: str | None = None,
    data_lineage_hash: str | None = None,
    quality_score: float | None = None,
    licensing_governance: str = "MIT-Data-Asset-v1"
) -> None:
    """Appends atomic execution logs to maintain structural audit paths with licensing governance."""
    cursor.execute("""
        INSERT INTO pipeline_execution_logs (
            run_id, step_name, status, execution_time, error_message, 
            data_lineage_hash, quality_score, licensing_governance
        )
        VALUES (?, ?, ?, datetime('now'), ?, ?, ?, ?);
    """, (run_id, step_name, status, error_message, data_lineage_hash, quality_score, licensing_governance))
