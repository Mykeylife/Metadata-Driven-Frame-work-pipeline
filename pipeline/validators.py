import sqlite3
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("pipeline.validators")

class DataQualityValidator:
    def __init__(self, db_path: str = "metadata_control.db"):
        self.db_path = db_path

    def _get_db_connection(self) -> sqlite3.Connection:
        """Helper to get a connection to the data layer."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def check_row_count(self, table_name: str, min_expected: int = 1) -> bool:
        """
        Gating Rule 1: Checks if a table has at least the minimum required records.
        Fails if the table is completely empty or falls below the threshold.
        """
        query = f"SELECT COUNT(*) FROM {table_name};"
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                row_count = cursor.fetchone()[0]
                
                if row_count >= min_expected:
                    logger.info(f"Quality Pass [Row Count]: {table_name} has {row_count} rows (Min required: {min_expected}).")
                    return True
                else:
                    logger.error(f"Quality Breach [Row Count]: {table_name} has only {row_count} rows! Expected minimum: {min_expected}.")
                    return False
        except sqlite3.OperationalError as e:
            logger.error(f"Quality Gating Failed: Table '{table_name}' does not exist or cannot be accessed: {e}")
            return False

    def check_null_threshold(self, table_name: str, column_name: str, max_allowed_pct: float = 0.0) -> bool:
        """
        Gating Rule 2: Verifies that critical primary/foreign key columns do not exceed 
        the maximum allowable percentage of NULL records.
        """
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
                    logger.warning(f"Quality Warning [Null Check]: {table_name} is empty. Skipping percentage evaluation.")
                    return True
                
                null_pct = (null_rows / total_rows) * 100.0
                if null_pct <= max_allowed_pct:
                    logger.info(f"Quality Pass [Null Check]: {table_name}.{column_name} is {null_pct:.2f}% NULL (Max allowed: {max_allowed_pct}%).")
                    return True
                else:
                    logger.error(f"Quality Breach [Null Check]: {table_name}.{column_name} is {null_pct:.2f}% NULL! Exceeds maximum: {max_allowed_pct}%.")
                    return False
        except sqlite3.OperationalError as e:
            logger.error(f"Quality Gating Failed: Column evaluation failed on {table_name}.{column_name}: {e}")
            return False

    def validate_step(self, task: Dict[str, Any]) -> bool:
        """
        Orchestrates all applicable data quality validations for a specific table step.
        Returns False immediately if any metric fails, acting as a strict operational gate.
        """
        target_table = task.get("target_table")
        if not target_table:
            logger.error("Validation bypassed: No target table specified in task parameters.")
            return False
            
        logger.info(f"Running data quality validation rules for target table: {target_table}")
        
        # Rule 1: Row count validation (requires at least 1 record post-load)
        if not self.check_row_count(target_table, min_expected=1):
            return False
            
        # Rule 2: Primary ID null verification (Strict 0% tolerance for null keys)
        # Note: You can expand this to look up critical fields dynamically from a schema map
        if not self.check_null_threshold(target_table, column_name="id", max_allowed_pct=0.0):
            return False
            
        return True
