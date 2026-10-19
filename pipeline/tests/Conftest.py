import os
import sqlite3

import pytest


@pytest.fixture
def clean_db_conn():
    """Dynamically seeds an in-memory SQLite database using the project DDL file."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Locate your script path regardless of where the runner evaluates the task
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sql_path = os.path.join(base_dir, "v1_init_metadata_tables.sql")

    # Fallback to root directory if conftest is located inside a nested /tests folder
    if not os.path.exists(sql_path):
        sql_path = os.path.join(os.path.dirname(base_dir), "v1_init_metadata_tables.sql")

    if os.path.exists(sql_path):
        # FIXED: Removed unnecessary "r" open mode parameter to satisfy UP015
        with open(sql_path) as f:
            sql_script = f.read()
        # Execute the entire script block (creating all 5 tables + seeding metadata records)
        cursor.executescript(sql_script)
    else:
        # Emergency raw backup initialization if file path resolution shifts inside CI
        cursor.execute(
            "CREATE TABLE pipeline_metadata (step_id INTEGER PRIMARY KEY, step_name TEXT UNIQUE, target_table TEXT, "
            "execution_order INTEGER, is_active INTEGER);"
        )
        cursor.execute(
            "CREATE TABLE pipeline_execution_logs (id INTEGER PRIMARY KEY, run_id TEXT, step_name TEXT, status TEXT, "
            "execution_time TEXT, error_message TEXT);"
        )
        cursor.execute("CREATE TABLE staging_users (id INTEGER PRIMARY KEY, username TEXT);")
        cursor.execute(
            "CREATE TABLE analytics_kpis (kpi_id INTEGER PRIMARY KEY, username TEXT, username_length INTEGER, "
            "processed_at TEXT);"
        )
        cursor.execute(
            "CREATE TABLE summary_metrics (summary_id INTEGER PRIMARY KEY, metric_name TEXT, metric_value TEXT, "
            "calculated_at TEXT);"
        )

    conn.commit()
    yield conn
    conn.close()
