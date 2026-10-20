"""Seeds runtime parameter catalogs out to infrastructure storage blocks."""

import json
import logging
import os
import sqlite3

from pipeline.config import get_db_path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed_metadata")

CONFIG_PATH = "config.json"


def seed_operational_matrix():
    """Parses local configuration tables and provisions metadata controls."""
    db_path = get_db_path()
    logger.info("Initializing metadata seeding cycle at configuration endpoint: %s", db_path)

    if not os.path.exists(CONFIG_PATH):
        logger.error("Configuration file resource not found: %s", CONFIG_PATH)
        return

    # FIXED: Replaced open mode parameters to follow UP015 conventions
    with open(CONFIG_PATH) as f:
        tasks = json.load(f)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for task in tasks.get("steps", []):
        cursor.execute("""
            INSERT OR IGNORE INTO pipeline_metadata (step_name, target_table, execution_order, is_active)
            VALUES (?, ?, ?, ?);
        """, (task["step_name"], task["target_table"], task["execution_order"], task.get("is_active", 1)))

    conn.commit()
    conn.close()
    logger.info("Database matrix seeded successfully.")


if __name__ == "__main__":
    seed_operational_matrix()
