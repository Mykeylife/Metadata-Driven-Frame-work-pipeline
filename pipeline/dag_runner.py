import logging
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Set up logger
logger = logging.getLogger("pipeline.dag_runner")


class DAGRunner:

    def __init__(self, db_path: str = "metadata_control.db"):
        self.db_path = db_path

    def _get_db_connection(self) -> sqlite3.Connection:
        """Creates and returns a connection to the SQLite simulation metadata store."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Access columns by name natively
        return conn

    def fetch_pipeline_tasks(self) -> List[Dict[str, Any]]:
        """Fetches active tasks from pipeline_metadata ordered by execution sequence."""
        query = """
            SELECT step_id, step_name, target_table, execution_order
            FROM pipeline_metadata
            WHERE is_active = 1
            ORDER BY execution_order ASC;
        """
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                tasks = [dict(row) for row in cursor.fetchall()]
                logger.info(f"Successfully retrieved {len(tasks)} tasks.")
                return tasks
        except sqlite3.OperationalError as e:
            logger.error(
                f"Database schema missing or misconfigured: {e}. Enforcing crash barrier."
            )
            raise

    def log_execution(
        self,
        run_id: str,
        step_name: str,
        status: str,
        error_message: Optional[str] = None,
    ) -> None:
        """Writes execution logs directly to pipeline_execution_logs to maintain tracking telemetry."""
        insert_query = """
            INSERT INTO pipeline_execution_logs (run_id, step_name, status, execution_time, error_message)
            VALUES (?, ?, ?, ?, ?);
        """
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                now_str = datetime.now(timezone.utc).isoformat()
                cursor.execute(
                    insert_query,
                    (run_id, step_name, status, now_str, error_message),
                )
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Failed to log execution state for step {step_name}: {e}")

    def execute_task_logic(self, task: Dict[str, Any]) -> bool:
        """Executes data operations and validates that target staging tables are populated."""
        target_table = task.get("target_table")
        
        if not target_table:
            logger.error("Task definition is missing an explicit 'target_table' parameter mapping.")
            return False

        logger.info(f"Initiating operational data quality validation gate for table: {target_table}")
        
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                # 1. Inspect database metadata schema to see if the table exists
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?;", 
                    (target_table,)
                )
                if not cursor.fetchone():
                    logger.error(f"Quality Gate Breach: Target table '{target_table}' does not exist in schema.")
                    return False
                
                # 2. Perform low-overhead conditional lookup to find out if the table is empty
                cursor.execute(f"SELECT 1 FROM {target_table} LIMIT 1;")
                if not cursor.fetchone():
                    logger.error(
                        f"Quality Gate Breach: Ingestion halted! Staging table '{target_table}' is completely empty."
                    )
                    return False
                    
            logger.info(f"Quality validation passed successfully for table: {target_table}")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Database error encountered during quality gate inspection on '{target_table}': {e}")
            return False

    def run_pipeline(self) -> None:
        """Orchestrates your end-to-end data pipeline flow based on metadata sequences."""
        run_id = str(uuid.uuid4())
        logger.info(
            f"Starting pipeline orchestration run sequence. Run reference UUID: {run_id}"
        )

        try:
            tasks = self.fetch_pipeline_tasks()
            if not tasks:
                logger.warning(
                    "No active pipeline metadata rows discovered matching criteria."
                )
                return

            for task in tasks:
                step_name = task.get("step_name", "UNKNOWN_STEP")
                logger.info(f"Initiating execution phase for step: {step_name}")

                # 1. Log running lifecycle state
                self.log_execution(run_id, step_name, "RUNNING")

                # 2. Execute target transformation/ingestion logic
                success = self.execute_task_logic(task)

                if success:
                    # 3. Handle successful runs
                    self.log_execution(run_id, step_name, "SUCCESS")
                    logger.info(f"Completed successfully: {step_name}")
                else:
                    # 4. Handle logical failure states
                    error_msg = "Task script executed but returned false"
                    self.log_execution(
                        run_id, step_name, "FAILED", error_message=error_msg
                    )
                    logger.error(
                        f"Pipeline flow stopped at step {step_name} due to verification fail."
                    )
                    break

        except Exception as global_err:
            logger.critical(
                f"Critical execution barrier reached during workflow handling: {global_err}"
            )
            self.log_execution(
                run_id, "GLOBAL_ORCHESTRATOR", "CRITICAL", str(global_err)
            )


if __name__ == "__main__":
    # Allows fast debugging execution directly via python pipeline/dag_runner.py
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    runner = DAGRunner()
    runner.run_pipeline()
