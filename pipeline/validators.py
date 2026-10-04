"""Data quality validation for pipeline execution."""
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class DataQualityValidator:
    """Validates data quality and database schema integrity."""

    def validate_atomic_schema(self, db_path: str) -> bool:
        """
        Validates that the database schema is properly initialized.
        
        Args:
            db_path: Path to the SQLite database.
            
        Returns:
            True if schema is valid, False otherwise.
        """
        try:
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check required tables exist
            required_tables = [
                'pipeline_metadata',
                'staging_users',
                'summary_metrics',
                'analytics_kpis'
            ]
            
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table';"
            )
            existing_tables = {row[0] for row in cursor.fetchall()}
            
            conn.close()
            
            missing_tables = set(required_tables) - existing_tables
            if missing_tables:
                logger.error(
                    "Missing required tables: %s", 
                    ', '.join(missing_tables)
                )
                return False
            
            logger.info("Database schema validation successful.")
            return True
            
        except Exception as e:
            logger.error("Schema validation failed: %s", str(e))
            return False

    def validate_row_record(
        self, 
        table_name: str, 
        row_data: Dict[str, Any]
    ) -> bool:
        """
        Validates a single row record for data quality.
        
        Args:
            table_name: Name of the table being validated.
            row_data: Dictionary containing the row data.
            
        Returns:
            True if row passes validation, False otherwise.
        """
        try:
            if not row_data:
                logger.warning("Empty row data provided for validation.")
                return False
            
            if table_name == "staging_users":
                if 'username' not in row_data:
                    logger.warning(
                        "Missing 'username' field in staging_users row."
                    )
                    return False
                
                username = row_data['username']
                if not username or not isinstance(username, str):
                    logger.warning(
                        "Invalid username value: %s", 
                        username
                    )
                    return False
            
            return True
            
        except Exception as e:
            logger.error(
                "Row validation failed for table %s: %s", 
                table_name, 
                str(e)
            )
            return False
