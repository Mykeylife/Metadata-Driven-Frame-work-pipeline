import json
import os
import sqlite3

# FIX (Item 3): Import the centralized database path configuration logic
from pipeline.config import get_db_path

DB_PATH = get_db_path()
CONFIG_PATH = "pipeline_config.json"

# FIX (Item 5): Centralize SQL structural DDL schemas into a single dictionary
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
        print(f"Error: Configuration file '{CONFIG_PATH}' not found.")
        return

    print(f"Reading pipeline configurations from '{CONFIG_PATH}'...")
    with open(CONFIG_PATH, "r") as f:
        tasks = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # FIX (Item 5): Natively iterate through centralized definitions to provision tables cleanly
    print("Enforcing centralized infrastructure database schemas...")
    for table_name, schema_ddl in TABLE_SCHEMAS.items():
        cursor.execute(schema_ddl)

    print(f"Seeding {len(tasks)} tasks into '{DB_PATH}'...")
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
    print("Database seeding completed successfully! ✅")


if __name__ == "__main__":
    seed_pipeline_database()
