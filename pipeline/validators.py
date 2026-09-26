import logging
import re
import sqlite3
from typing import Any, Dict

logger = logging.getLogger("pipeline.validators")


class DataQualityValidator:

    def __init__(self, db_path: str = "metadata_control.db"):
        self.db_path = db_path

        # Blueprint matrix mapping expected columns and types for boot checking
        self.expected_schemas = {
            "pipeline_metadata": {
                "step_id": "INTEGER",
                "step_name": "TEXT",
                "target_table": "TEXT",
                "execution_order": "INTEGER",
                "is_active": "INTEGER",
            },
            "pipeline_execution_logs": {
                "id": "INTEGER",
                "run_id": "TEXT",
                "step_name": "TEXT",
                "status": "TEXT",
                "execution_time": "TEXT",
                "peak_memory_kb": "INTEGER",
                "cpu_time_seconds": "REAL",
                "error_message": "TEXT",
            },
            "staging_users": {"id": "INTEGER", "username": "TEXT"},
            "analytics_kpis": {
                "kpi_id": "INTEGER",
                "username": "TEXT",
                "username_length": "INTEGER",
                "processed_at": "TEXT",
            },
            "summary_metrics": {
                "summary_id": "INTEGER",
                "metric_name": "TEXT",
                "metric_value": "TEXT",
                "calculated_at": "TEXT",
            },
        }

    def _get_db_connection(self) -> sqlite3.Connection:
        """Helper to get a connection to the data layer."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def check_schema_alignment(self, table_name: str) -> bool:
        """Gating Rule 0: Validates that database column structures match production

        blueprints exactly on boot.
        """
        expected = self.expected_schemas.get(table_name)
        if not expected:
            logger.info(f"Schema check bypassed: No mapping for '{table_name}'.")
            return True

        query = f"PRAGMA table_info({table_name});"
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                columns = cursor.fetchall()

                if not columns:
                    logger.error(f"Schema Breach: Table '{table_name}' empty/missing.")
                    return False

                actual_schema = {row["name"]: row["type"] for row in columns}

                # Verify column names and data types align
                for col_name, col_type in expected.items():
                    if col_name not in actual_schema:
                        logger.error(
                            f"Schema Breach: Column '{col_name}' missing "
                            f"in table '{table_name}'."
                        )
                        return False
                    if actual_schema[col_name] != col_type:
                        logger.error(
                            f"Schema Breach: Column '{col_name}' type mismatch in "
                            f"'{table_name}'. Expected {col_type}, "
                            f"got {actual_schema[col_name]}."
                        )
                        return False

                logger.info(f"Quality Pass [Schema]: '{table_name}' structure aligns.")
                return True
        except sqlite3.OperationalError as e:
            logger.error(f"Schema validation failed on '{table_name}': {e}")
            return False

    def check_row_count(self, table_name: str, min_expected: int = 1) -> bool:
        """Gating Rule 1: Checks if a table has at least the minimum required records."""
        query = f"SELECT COUNT(*) FROM {table_name};"
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                row_count = cursor.fetchone()[0]
                
                if row_count >= min_expected:
                    logger.info(
                        f"Quality Pass [Row Count]: {table_name} has {row_count} rows "
                        f"(Min required: {min_expected})."
                    )
                    return True
                else:
                    logger.error(
                        f"Quality Breach [Row Count]: {table_name} has only {row_count} "
                        f"rows! Expected minimum: {min_expected}."
                    )
                    return False
        except sqlite3.OperationalError as e:
            logger.error(f"Quality Gating Failed: Table '{table_name}' inaccessible: {e}")
            return False

    def check_null_threshold(
        self, table_name: str, column_name: str, max_allowed_pct: float = 0.0
    ) -> bool:
        """Gating Rule 2: Verifies critical columns do not exceed null limits."""
        query = f"""
            SELECT 
                COUNT(*) as total_rows,
                SUM(CASE WHEN {column_name} IS NULL THEN 1 ELSE 0 END) as null_rows
            FROM {table_name};
        """
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                row = cursor.fetchone()
                
                total_rows = row["total_rows"]
                null_rows = row["null_rows"] if row["null_rows"] is not None else 0
                
                if total_rows == 0:
                    logger.warning(
                        f"Quality Warning [Null Check]: {table_name} is empty. "
                        f"Skipping evaluation."
                    )
                    return True
                
                null_pct = (null_rows / total_rows) * 100.0
                if null_pct <= max_allowed_pct:
                    logger.info(
                        f"Quality Pass [Null Check]: {table_name}.{column_name} is "
                        f"{null_pct:.2f}% NULL (Max: {max_allowed_pct}%)."
                    )
                    return True
                else:
                    logger.error(
                        f"Quality Breach [Null Check]: {table_name}.{column_name} is "
                        f"{null_pct:.2f}% NULL! Exceeds maximum: {max_allowed_pct}%."
                    )
                    return False
        except sqlite3.OperationalError as e:
            logger.error(f"Quality Gating Failed: Evaluation failed on {table_name}: {e}")
            return False

    def check_syntax_constraints(self, table_name: str, column_name: str) -> bool:
        """Gating Rule 3: Validates that strings inside character columns adhere to clean

        alphanumeric, underscore, or hyphen constraints (3-20 characters).
        """
        query = f"SELECT {column_name} FROM {table_name};"
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                rows = cursor.fetchall()
                
                for row in rows:
                    val = row[column_name]
                    if not val or not re.match(r"^[a-zA-Z0-9_\-]{3,20}$", str(val)):
                        logger.error(
                            f"Quality Breach [Syntax Check]: Value '{val}' in "
                            f"{table_name}.{column_name} is invalid."
                        )
                        return False
                        
                logger.info(
                    f"Quality Pass [Syntax Check]: All records in "
                    f"{table_name}.{column_name} conform to syntax filters."
                )
                return True
        except sqlite3.OperationalError as e:
            logger.error(f"Gating Failed: Syntax check skipped on {table_name}: {e}")
            return False

    def validate_step(self, task: Dict[str, Any]) -> bool:
        """Orchestrates all applicable data quality validations for a specific table step."""
        target_table = task.get("target_table")
        if not target_table:
            logger.error("Validation bypassed: No target table specified.")
            return False
            
        logger.info(f"Running data quality rules for table: {target_table}")
        
        # Rule 0: Atomic schema structure alignment validation
        if not self.check_schema_alignment(target_table):
            return False

        # Rule 1: Row count validation (requires at least 1 record post-load)
        if not self.check_row_count(target_table, min_expected=1):
            return False
            
        primary_key_map = {
            "staging_users": "id",
            "analytics_kpis": "kpi_id",
            "summary_metrics": "summary_id",
        }
        pk_column = primary_key_map.get(target_table, "id")

        # Rule 2: Primary ID null verification (Strict 0% tolerance for null keys)
        if not self.check_null_threshold(
            target_table, column_name=pk_column, max_allowed_pct=0.0
        ):
            return False
            
        # Rule 3: Run targeted syntax character regex pattern matching on source data
        if target_table == "staging_users":
            if not self.check_syntax_constraints(target_table, column_name="username"):
                return False
                
        return True
