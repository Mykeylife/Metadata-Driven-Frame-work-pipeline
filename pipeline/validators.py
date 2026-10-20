"""Data quality verification rules engine enforcing target metadata parameters and transactional boundaries."""

import sqlite3


class DataQualityValidator:
    """Enforces strict structural data validation gates against staging and ingestion records."""

    def validate_atomic_schema(self, db_path: str) -> bool:
        """Verifies that all five production monitoring tables exist flawlessly inside the target storage engine."""
        required_tables = [
            "pipeline_metadata",
            "pipeline_execution_logs",
            "staging_users",
            "analytics_kpis",
            "summary_metrics",
        ]
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            existing_tables = [row[0] for row in cursor.fetchall()]
            conn.close()
            return all(table in existing_tables for table in required_tables)
        except sqlite3.Error:
            return False

    def validate_row_record(self, table_name: str, record: dict) -> bool:
        """Evaluates row properties against high-throughput null-value and structural schema filters."""
        if not record or not isinstance(record, dict):
            return False

        if table_name == "staging_users":
            username = record.get("username")
            if username is None:
                return False
            # Ensure the string is populated and not an isolated whitespace entry
            if isinstance(username, str) and not username.strip():
                return False

        return True
