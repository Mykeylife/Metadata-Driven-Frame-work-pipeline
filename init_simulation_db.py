import logging
import sqlite3
import os

try:
    from pipeline.config import get_db_path
except ModuleNotFoundError:
    from config import get_db_path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("init_simulation_db")

DB_PATH = get_db_path()

def initialize_database() -> None:
    """Creates local data-plane tables and seeds active metadata configurations."""
    logger.info("Initializing local simulation database at '%s'...", DB_PATH)
    
    # Ensure directory exists
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Create Control Matrix Metadata Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_metadata (
            step_id INTEGER PRIMARY KEY AUTOINCREMENT,
            step_name TEXT NOT NULL UNIQUE,
            target_table TEXT NOT NULL,
            execution_order INTEGER NOT NULL,
            is_active INTEGER DEFAULT 1
        );
    """)

    # NEW: Centralized Local Audit Store Table (Telemetry Metrics Warehouse)
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

    # 2. Create Target Data Tables
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
            metric_name TEXT NOT NULL UNIQUE,
            metric_value TEXT NOT NULL,
            calculated_at TEXT NOT NULL
        );
    """)

    # 3. Seed Metadata Control Configurations
    logger.info("Seeding pipeline control steps...")
    cursor.executemany("""
        INSERT OR IGNORE INTO pipeline_metadata (step_name, target_table, execution_order, is_active)
        VALUES (?, ?, ?, ?);
    """, [
        ("Process Users Staging", "staging_users", 10, 1),
        ("Aggregate Analytics Metrics", "summary_metrics", 20, 1)
    ])

    # 4. Seed Clean Mock Production Users
    logger.info("Seeding initial staging user data records...")
    cursor.execute("DELETE FROM staging_users;")  # Clear out stale rows
    cursor.executemany("""
        INSERT INTO staging_users (username) VALUES (?);
    """, [
        ("micheal_akinbode",),
        ("jessica_akinbode",),
        ("olalanrewaju_dev",),
        ("corrupted_record_test_   ",),  # Edge case spaces to test validators
    ])

    conn.commit()
    conn.close()
    logger.info("Database simulation environment successfully initialized! ✅")

if __name__ == "__main__":
    initialize_database()
