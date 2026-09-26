import os
import sqlite3

# Align directly with the DEFAULT_DB_PATH constant in pipeline/config.py
DEFAULT_DB_PATH = "metadata_control.db"


def init_db(db_path: str = DEFAULT_DB_PATH):
    """Initializes and seeds the production-grade metadata and business simulation tables."""
    print(f"Initializing centralized core data schemas inside: {db_path}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Core Sequence Control Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_metadata (
            step_id INTEGER PRIMARY KEY AUTOINCREMENT,
            step_name TEXT NOT NULL UNIQUE,
            target_table TEXT NOT NULL,
            execution_order INTEGER NOT NULL,
            is_active INTEGER DEFAULT 1
        );
    """)

    # 2. Comprehensive Telemetry Audit Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_execution_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            step_name TEXT NOT NULL,
            status TEXT NOT NULL,
            execution_time TEXT NOT NULL,
            peak_memory_kb INTEGER DEFAULT 0,
            cpu_time_seconds REAL DEFAULT 0.0,
            error_message TEXT
        );
    """)

    # 3. Source Business Data Ingestion Layer
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS staging_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE
        );
    """)

    # 4. Transformed KPI Processing Layer
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analytics_kpis (
            kpi_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            username_length INTEGER NOT NULL,
            processed_at TEXT NOT NULL
        );
    """)

    # 5. Core Aggregated Reporting Layer
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS summary_metrics (
            summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_name TEXT NOT NULL UNIQUE,
            metric_value TEXT NOT NULL,
            calculated_at TEXT NOT NULL
        );
    """)

    # --- CONTROL LAYER DATA SEEDING ---
    print("Seeding workflow orchestration sequence mappings...")
    tasks_to_seed = [
        ("Extract Raw Staging Users", "staging_users", 10),
        ("Process Metric Analytics KPIs", "analytics_kpis", 20),
        ("Compile Reporting Summary Metrics", "summary_metrics", 30),
    ]
    for step_name, target_table, execution_order in tasks_to_seed:
        cursor.execute("""
            INSERT OR IGNORE INTO pipeline_metadata (step_name, target_table, execution_order, is_active)
            VALUES (?, ?, ?, 1);
        """, (step_name, target_table, execution_order))

    # --- BUSINESS WORKSPACE RECORDS SEEDING ---
    print("Injecting initial staging profiles to fulfill processing gates...")
    sample_users = [("Olanrewaju",), ("Myke",), ("PipelineDev",)]
    cursor.executemany("""
        INSERT OR IGNORE INTO staging_users (username) VALUES (?);
    """, sample_users)

    conn.commit()
    conn.close()
    print("Database environment completely provisioned and ready for pipeline activation!")


if __name__ == "__main__":
    init_db()
