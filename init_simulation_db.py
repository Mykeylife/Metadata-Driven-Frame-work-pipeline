"""Provisions the baseline transactional environment schemas and structural execution seeds offline."""

import logging
import os
import sqlite3

from pipeline.config import get_db_path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("init_simulation_db")


def init_db() -> None:
    """Applies the production DDL blueprint configuration records directly to the SQLite control store."""
    db_path = get_db_path()
    logger.info("Initializing metadata-driven control database setup sequence at: %s", db_path)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    sql_path = os.path.join(base_dir, "v1_init_metadata_tables.sql")

    if not os.path.exists(sql_path):
        sql_path = os.path.join(base_dir, "pipeline", "v1_init_metadata_tables.sql")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    if os.path.exists(sql_path):
        with open(sql_path) as f:
            sql_script = f.read()
        cursor.executescript(sql_script)
        logger.info("Database schemas initialized cleanly using v1_init_metadata_tables.sql blueprint.")
    else:
        logger.warning("DDL initialization script not discovered at endpoint. Applying fallback scaffold layout.")
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS pipeline_metadata (
                step_id INTEGER PRIMARY KEY AUTOINCREMENT,
                step_name TEXT NOT NULL UNIQUE,
                target_table TEXT NOT NULL,
                execution_order INTEGER NOT NULL,
                is_active INTEGER DEFAULT 1
            );
        """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS pipeline_execution_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                step_name TEXT NOT NULL,
                status TEXT NOT NULL,
                execution_time TEXT NOT NULL,
                error_message TEXT,
                data_lineage_hash TEXT,
                quality_score REAL,
                licensing_governance TEXT DEFAULT 'MIT-Data-Asset-v1'
            );
        """
        )

    conn.commit()
    conn.close()
    logger.info("Database simulation initialization sequence successfully completed.")


if __name__ == "__main__":
    init_db()
