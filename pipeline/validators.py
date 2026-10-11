"""Data quality validation for pipeline execution."""

import logging
import sqlite3

logger = logging.getLogger(__name__)


class DataQualityValidator:
    """Validates structural database health parameters and operational row integrity."""

    def validate_atomic_schema(self, db_path: str) -> bool:
        """Verifies database availability and base structural constraints."""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()
            return "pipeline_metadata" in tables
        except sqlite3.Error as e:
            logger.error(f"Schema tracking baseline verification collapsed: {e}")
            return False

    def validate_row_record(self, table_name: str, row: dict) -> bool:
        """Ensures incoming data rows pass non-null boundary validation criteria."""
        if table_name == "staging_users":
            return bool(row and row.get("username") and str(row["username"]).strip())
        return True
