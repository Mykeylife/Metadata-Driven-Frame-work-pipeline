import json
import os
import sqlite3

DB_PATH = "metadata_control.db"
CONFIG_PATH = "pipeline_config.json"


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

    # 1. Enforce schema existence for core control metadata
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_metadata (
            step_id INTEGER PRIMARY KEY AUTOINCREMENT,
            step_name TEXT NOT NULL,
            target_table TEXT NOT NULL,
            execution_order INTEGER NOT NULL,
            is_active INTEGER DEFAULT 1
        );
    """)

    # 2. Pre-create business data infrastructure staging tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS staging_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL
        );
    """)

    # 3. Create the concrete target analytics KPI storage schema
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analytics_kpis (
            kpi_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            username_length INTEGER NOT NULL,
            processed_at TEXT NOT NULL
        );
    """)

    print(f"Seeding {len(tasks)} tasks into '{DB_PATH}'...")
    for task in tasks:
        # Clear down existing mapping flags cleanly to allow updates on identical rows
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
