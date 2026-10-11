"""Initializes the local SQLite simulation database schema with baseline metadata."""

import logging
import os
import sqlite3

from pipeline.config import get_db_path

logger = logging.getLogger("init_simulation_db")


def init_db(db_path: str = None) -> None:
    """Creates local data tables and seeds baseline operational configurations."""
    if not db_path:
        db_path = get_db_path()

    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)

    logger.info(f"Initializing local simulation database at '{db_path}'...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Core control store table creation rules
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_metadata (
            step_id INTEGER PRIMARY KEY AUTOINCREMENT,
            step_name TEXT NOT NULL UNIQUE,
            target_table TEXT NOT NULL,
            execution_order INTEGER NOT NULL,
            is_active INTEGER DEFAULT 1
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_execution_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            step_name TEXT NOT NULL,
            status TEXT NOT NULL,
            execution_time TEXT NOT NULL,
            peak_memory_kb INTEGER,
            cpu_time_seconds REAL,
            error_message TEXT
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS staging_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analytics_kpis (
            kpi_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            username_length INTEGER NOT NULL,
            processed_at TEXT NOT NULL
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS summary_metrics (
            summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_name TEXT NOT NULL,
            metric_value TEXT NOT NULL,
            calculated_at TEXT NOT NULL
        );
    """)

    # Seed initial tracking operational rows
    cursor.executemany("""
        INSERT OR IGNORE INTO pipeline_metadata (step_id, step_name, target_table, execution_order, is_active)
        VALUES (?, ?, ?, ?, ?);
    """, [
        (1, "Load Staging Users Data", "staging_users", 1, 1),
        (2, "Aggregate Analytics Metrics", "summary_metrics", 2, 1)
    ])

    cursor.executemany("""
        INSERT OR IGNORE INTO staging_users (id, username)
        VALUES (?, ?);
    """, [
        (1, "alex_dataops"),
        (2, "beatrice_eng"),
        (3, "charlie_alpha")
    ])

    conn.commit()
    conn.close()
    logger.info("Database initialization completed cleanly.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    init_db()
