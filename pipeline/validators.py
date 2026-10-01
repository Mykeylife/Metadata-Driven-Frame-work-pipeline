import logging
import sqlite3
from typing import Dict, List, Set, Tuple

logger = logging.getLogger("validators")

class DataQualityValidator:
    """Provides atomic schema validation and structural data quality gating rules."""

    def __init__(self) -> None:
        # Define expected production table schemas for validation checks
        self.expected_schemas: Dict[str, Set[str]] = {
            "staging_users": {"id", "username"},
            "analytics_kpis": {"kpi_id", "username", "username_length", "processed_at"},
            "summary_metrics": {"summary_id", "metric_name", "metric_value", "calculated_at"}
        }

    def validate_atomic_schema(self, db_path: str) -> bool:
        """Checks the underlying database tables on boot to verify all critical columns exist."""
        logger.info("Initializing atomic database schema verification sweep...")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            for table_name, expected_columns in self.expected_schemas.items():
                # Query table structural information metadata natively
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns_meta: List[Tuple] = cursor.fetchall()
                
                if not columns_meta:
                    logger.error("Structural rule failure: Target table '%s' does not exist in schema.", table_name)
                    conn.close()
                    return False
                
                # Extract clean column name strings
                actual_columns: Set[str] = {col[1] for col in columns_meta}
                
                # Check for missing column dependencies
                missing_columns: Set[str] = expected_columns - actual_columns
                if missing_columns:
                    logger.error(
                        "Schema mismatch detected on '%s'! Missing required fields: %s",
                        table_name, missing_columns
                    )
                    conn.close()
                    return False
                    
            logger.info("All atomic structural schema layers successfully validated ✅")
            conn.close()
            return True
            
        except Exception as e:
            logger.error("Critical error during schema validation sweep: %s", str(e))
            return False

    def validate_row_record(self, table_name: str, row_data: Dict[str, any]) -> bool:
        """Validates individual column payload integrity rules before row transformation steps."""
        if table_name not in self.expected_schemas:
            return True
            
        # Ensure mandatory structural payload schemas match target domains exactly
        if table_name == "staging_users":
            username = row_data.get("username")
            if not username or str(username).strip() == "":
                logger.warning("Data quality anomaly: Encountered null or empty username record.")
                return False
                
        return True
