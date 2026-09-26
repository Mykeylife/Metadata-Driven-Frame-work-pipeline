import json
import logging
import sqlite3
import time
import urllib.request
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Import the centralized configuration vectors
from pipeline.config import get_db_path, get_webhook_url

# Set up logger
logger = logging.getLogger("pipeline.dag_runner")


class DAGRunner:

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path if db_path is not None else get_db_path()

    def _get_db_connection(self) -> sqlite3.Connection:
        """Creates and returns a connection to the SQLite simulation metadata store."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _send_webhook_alert(self, run_id: str, step_name: str, status: str, error_message: Optional[str]) -> None:
        """Transmits high-priority execution warnings asynchronously to a Discord/Slack webhook target."""
        webhook_url = get_webhook_url()
        if not webhook_url:
            return  # Fail gracefully if notifications aren't provisioned locally

        # Generate a universal cross-platform notification payload layout block
        payload = {
            "content": f"⚠️ **Pipeline Alert Breach**\n"
                       f"• **Run ID:** `{run_id}`\n"
                       f"• **Step Target:** `{step_name}`\n"
                       f"• **Failure Status:** `{status}`\n"
                       f"• **Log Trace:** `{error_message or 'No specific message trace recorded.'}`"
        }
        
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                webhook_url,
                data=data,
                headers={"Content-Type": "application/json", "User-Agent": "PipelineOrchestrator/1.0"}
            )
            # Execute standard platform data post request wrapper
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status not in (200, 204):
                    logger.warning(f"Notification alert target returned unexpected state code: {response.status}")
        except Exception as err:
            logger.error(f"Failed to transmit live telemetry operational webhook notification log: {err}")

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
            logger.error(f"Database schema missing or misconfigured: {e}. Enforcing crash barrier.")
            raise

    def log_execution(
        self,
        run_id: str,
        step_name: str,
        status: str,
        execution_time: str = "N/A",
        error_message: Optional[str] = None,
    ) -> None:
        """Writes execution logs directly to database telemetry and alerts phone on anomalies."""
        insert_query = """
            INSERT INTO pipeline_execution_logs (run_id, step_name, status, execution_time, error_message)
            VALUES (?, ?, ?, ?, ?);
        """
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    insert_query,
                    (run_id, step_name, status, execution_time, error_message),
                )
                conn.commit()
            
            # FIX: Trigger instant phone webhook alert if a task drops or fails metrics gates
            if status in ("FAILED", "CRITICAL"):
                self._send_webhook_alert(run_id, step_name, status, error_message)
                
        except sqlite3.Error as e:
            logger.error(f"Failed to log execution state for step {step_name}: {e}")

    def execute_task_logic(self, task: Dict[str, Any]) -> bool:
        """Executes data operations, processes KPI transformations, or validates table status."""
        target_table = task.get("target_table")
        
        if not target_table:
            logger.error("Task definition is missing an explicit 'target_table' parameter mapping.")
            return False

        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (target_table,))
                if not cursor.fetchone():
                    logger.error(f"Quality Gate Breach: Target table '{target_table}' does not exist in schema.")
                    return False
                
                if target_table == "analytics_kpis":
                    logger.info("Running real data calculation loop for analytics_kpis...")
                    cursor.execute("SELECT username FROM staging_users;")
                    users = cursor.fetchall()
                    
                    if not users:
                        logger.error("Quality Gate Breach: Extraction halted! Source 'staging_users' table has no records.")
                        return False
                        
                    now_str = datetime.now(timezone.utc).isoformat()
                    for user in users:
                        username = user["username"]
                        cursor.execute(
                            "INSERT INTO analytics_kpis (username, username_length, processed_at) VALUES (?, ?, ?);",
                            (username, len(username), now_str)
                        )
                    conn.commit()
                    logger.info(f"Successfully processed metrics for {len(users)} users inside analytics_kpis.")
                
                elif target_table == "summary_metrics":
                    logger.info("Running aggregation calculation engine for summary_metrics...")
                    cursor.execute("SELECT MAX(username_length) as max_len FROM analytics_kpis;")
                    row = cursor.fetchone()
                    max_length = row["max_len"] if (row and row["max_len"] is not None) else 0
                    
                    now_str = datetime.now(timezone.utc).isoformat()
                    cursor.execute(
                        "INSERT INTO summary_metrics (metric_name, metric_value, calculated_at) VALUES (?, ?, ?);",
                        ("max_username_length", str(max_length), now_str)
                    )
                    conn.commit()
                    logger.info(f"Successfully calculated pipeline aggregations. Max length metric found: {max_length}")

                else:
                    logger.info(f"Initiating operational validation gate for staging table: {target_table}")
                    cursor.execute(f"SELECT 1 FROM {target_table} LIMIT 1;")
                    if not cursor.fetchone():
                        logger.error(f"Quality Gate Breach: Ingestion halted! Table '{target_table}' is empty.")
                        return False
                    
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Database error encountered during logic execution on '{target_table}': {e}")
            return False

    def run_pipeline(self) -> None:
        """Orchestrates your end-to-end data pipeline flow based on metadata sequences."""
        run_id = str(uuid.uuid4())
        logger.info(f"Starting pipeline orchestration run sequence. Run reference UUID: {run_id}")

        try:
            tasks = self.fetch_pipeline_tasks()
            if not tasks:
                logger.warning("No active pipeline metadata rows discovered matching criteria.")
                return

            for task in tasks:
                step_name = task.get("step_name", "UNKNOWN_STEP")
                logger.info(f"Initiating execution phase for step: {step_name}")

                self.log_execution(run_id, step_name, "RUNNING", execution_time=datetime.now(timezone.utc).isoformat())

                start_timer = time.perf_counter()
                success = self.execute_task_logic(task)
                end_timer = time.perf_counter()
                
                duration_str = f"{(end_timer - start_timer):.2f} seconds"

                if success:
                    self.log_execution(run_id, step_name, "SUCCESS", execution_time=duration_str)
                    logger.info(f"Completed successfully: {step_name} in {duration_str}")
                else:
                    error_msg = "Task script executed but returned false"
                    self.log_execution(
                        run_id=run_id,
                        step_name=step_name,
                        status="FAILED",
                        execution_time=duration_str,
                        error_message=error_msg,
                    )
                    logger.error(f"Pipeline flow stopped at step {step_name} due to verification fail.")
                    break

        except Exception as global_err:
            logger.critical(f"Critical execution barrier reached during workflow handling: {global_err}")
            self.log_execution(
                run_id, "GLOBAL_ORCHESTRATOR", "CRITICAL", execution_time="N/A", error_message=str(global_err)
            )


def main() -> None:
    """Standalone module function serving as the entrypoint for Poetry scripts command handles."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
