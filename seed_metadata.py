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

    # Enforce schema existence in case the database is completely empty
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_metadata (
            step_id INTEGER PRIMARY KEY AUTOINCREMENT,
            step_name TEXT NOT NULL,
            target_table TEXT NOT NULL,
            execution_order INTEGER NOT NULL,
            is_active INTEGER DEFAULT 1
        );
    """)

    print(f"Seeding {len(tasks)} tasks into '{DB_PATH}'...")
    for task in tasks:
        # Avoid duplicate steps by updating parameters if the step_name already exists
        cursor.execute(
            """
            INSERT INTO pipeline_metadata (step_name, target_table, execution_order, is_active)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(step_id) DO UPDATE SET
                target_table=excluded.target_table,
                execution_order=excluded.execution_order,
                is_active=excluded.is_active;
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
