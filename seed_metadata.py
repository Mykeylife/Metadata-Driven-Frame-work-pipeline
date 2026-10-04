import json
import logging
import os
import sqlite3
from pipeline.config import get_db_path

# Configure structured production-ready terminal logging framework
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("metadata_seeder")

DB_PATH = get_db_path()
CONFIG_PATH = "pipeline_config.json"

TABLE_SCHEMAS = {
    "pipeline_metadata": """
        CREATE TABLE IF NOT EXISTS pipeline_metadata (
            step_id INTEGER PRIMARY KEY AUTOINCREMENT,
            step_name TEXT NOT NULL,
            target_table TEXT NOT NULL,
            execution_order INTEGER NOT NULL,
            is_active INTEGER DEFAULT 1
        );
    """,
    "pipeline_execution_logs": """
        CREATE TABLE IF NOT EXISTS pipeline_execution_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            step_name TEXT NOT NULL,
            status TEXT NOT NULL,
            execution_time TEXT NOT NULL,
            error_message TEXT
        );
    """,
    "staging_users": """
        CREATE TABLE IF NOT EXISTS staging_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL
        );
    """,
    "analytics_kpis": """
        CREATE TABLE IF NOT EXISTS analytics_kpis (
            kpi_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            username_length INTEGER NOT NULL,
            processed_at TEXT NOT NULL
        );
    """,
    "summary_metrics": """
        CREATE TABLE IF NOT EXISTS summary_metrics (
            summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_name TEXT NOT NULL,
            metric_value TEXT NOT NULL,
            calculated_at TEXT NOT NULL
        );
    """
}

def seed_pipeline_database() -> None:
    """Reads configuration rules from a JSON file and seeds the SQLite control tables."""
    if not os.path.exists(CONFIG_PATH):
        logger.error("Configuration file '%s' not found.", CONFIG_PATH)
        return

    logger.info("Reading pipeline configurations from '%s'...", CONFIG_PATH)
    with open(CONFIG_PATH, "r") as f:
        tasks = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    logger.info("Enforcing centralized infrastructure database schemas...")
    for _table_name, schema_ddl in TABLE_SCHEMAS.items():
        cursor.execute(schema_ddl)

    logger.info("Seeding %d tasks into '%s'...", len(tasks), DB_PATH)
    for task in tasks:
        cursor.execute("DELETE FROM pipeline_metadata WHERE step_name = ?;", (task["step_name"],))
        cursor.execute(
            """
            INSERT INTO pipeline_metadata (step_name, target_table, execution_order, is_active)
            VALUES (?, ?, ?, ?);
            """,
            (
                task["step_name"],
                task["target_table"],
                task["execution_order"],
                task["is_active"],
            ),
        )

    conn.commit()
    conn.close()
    logger.info("Database seeding completed successfully! ✅")

if __name__ == "__main__":
    seed_pipeline_database()
