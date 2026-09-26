import json
import logging
import resource
import sqlite3
import time
import urllib.request
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Import centralized configuration parameters and validators
from pipeline.config import get_db_path, get_webhook_url
from pipeline.validators import DataQualityValidator

# Set up logger
logger = logging.getLogger("pipeline.dag_runner")


class DAGRunner:

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path if db_path is not None else get_db_path()
        # Initialize our automated quality gating engine
        self.validator = DataQualityValidator(db_path=self.db_path)

    def _get_db_connection(self) -> sqlite3.Connection:
        """Creates and returns a connection to the SQLite simulation store."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _send_webhook_alert(
        self, run_id: str, step_name: str, status: str, error_msg: Optional[str]
    ) -> None:
        """Transmits high-priority execution warnings asynchronously."""
        webhook_url = get_webhook_url()
        if not webhook_url:
            return

        payload = {
            "content": f"⚠️ **Pipeline Alert Breach**\n"
                       f"• **Run ID:** `{run_id}`\n"
                       f"• **Step Target:** `{step_name}`\n"
                       f"• **Failure Status:** `{status}`\n"
                       f"• **Log Trace:** `{error_msg or 'No trace recorded.'}`"
        }
        
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                webhook_url,
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "PipelineOrchestrator/1.0",
                },
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status not in (200, 204):
                    logger.warning(
                        f"Unexpected webhook response code: {response.status}"
                    )
        except Exception as err:
            logger.error(f"Failed to transmit telemetry webhook: {err}")

    def fetch_pipeline_tasks(self) -> List[Dict[str, Any]]:
        """Fetches active tasks from metadata ordered by execution sequence."""
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
            logger.error(f"Schema missing or misconfigured: {e}.")
            raise

    def log_execution(
        self,
        run_id: str,
        step_name: str,
        status: str,
        execution_time: str = "N/A",
        error_message: Optional[str] = None,
    ) -> None:
        """Writes execution logs directly to database telemetry."""
        usage = resource.getrusage(resource.RUSAGE_SELF)
        peak_mem = usage.ru_maxrss
        cpu_time = usage.ru_utime + usage.ru_stime

        insert_query = """
            INSERT INTO pipeline_execution_logs 
            (run_id, step_name, status, execution_time, 
             peak_memory_kb, cpu_time_seconds, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    insert_query,
                    (
                        run_id,
                        step_name,
                        status,
                        execution_time,
                        peak_mem,
                        cpu_time,
                        error_message,
                    ),
                )
                conn.commit()
            
            if status in ("FAILED", "CRITICAL"):
                self._send_webhook_alert(
                    run_id, step_name, status, error_message
                )
                
        except sqlite3.Error as e:
            logger.error(f"Failed to log execution state for {step_name}: {e}")

    def execute_task_logic(self, task: Dict[str, Any]) -> bool:
        """Executes data operations or validates table status frameworks."""
        target_table = task.get("target_table")
        step_name = task.get("step_name", "Unknown Step")
        
        if not target_table:
            logger.error("Task definition is missing 'target_table'.")
            return False

        # --- LIVE DATA QUALITY GATE BREACH BARRIER ---
        self.validator._get_db_connection = self._get_db_connection
        if not self.validator.validate_step(task):
            msg = (
                f"Quality Gate Breach: Validations failed for step "
                f"'{step_name}' on table '{target_table}'."
            )
            logger.error(msg)
            return False

        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                if target_table == "analytics_kpis":
                    logger.info("Running calculation loop for analytics_kpis...")
                    cursor.execute("SELECT username FROM staging_users;")
                    users = cursor.fetchall()
                    
                    now_str = datetime.now(timezone.utc).isoformat()
                    for user in users:
                        username = user["username"]
                        cursor.execute(
                            "INSERT INTO analytics_kpis "
                            "(username, username_length, processed_at) "
                            "VALUES (?, ?, ?);",
                            (username, len(username), now_str),
                        )
                    conn.commit()
                    logger.info(f"Processed metrics for {len(users)} users.")
                
                elif target_table == "summary_metrics":
                    logger.info("Running aggregation loop for summary_metrics...")
                    cursor.execute(
                        "SELECT MAX(username_length) as max_len "
                        "FROM analytics_kpis;"
                    )
                    row = cursor.fetchone()
                    max_length = (
                        row["max_len"]
                        if (row and row["max_len"] is not None)
                        else 0
                    )
                    
                    now_str = datetime.now(timezone.utc).isoformat()
                    cursor.execute(
                        "INSERT INTO summary_metrics "
                        "(metric_name, metric_value, calculated_at) "
                        "VALUES (?, ?, ?);",
                        ("max_username_length", str(max_length), now_str),
                    )
                    conn.commit()
                    logger.info(f"Aggregations complete. Max: {max_length}")

                else:
                    logger.info(f"Validating staging table: {target_table}")
                    cursor.execute(f"SELECT 1 FROM {target_table} LIMIT 1;")
                    if not cursor.fetchone():
                        logger.error(f"Gate Breach: '{target_table}' empty.")
                        return False
                    
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Database error on '{target_table}': {e}")
            return False

    def run_pipeline(self) -> None:
        """Orchestrates your end-to-end data pipeline flow sequences."""
        run_id = str(uuid.uuid4())
        msg = f"Starting orchestration run reference UUID: {run_id}"
        logger.info(msg)

        try:
            tasks = self.fetch_pipeline_tasks()
            if not tasks:
                logger.warning("No active pipeline metadata rows discovered.")
                return

            for task in tasks:
                step_name = task["step_name"]
                logger.info(f"Orchestrating operational task: {step_name}")
                
                start_time = time.time()
                self.log_execution(run_id, step_name, "RUNNING")
                
                success = self.execute_task_logic(task)
                duration_str = f"{time.time() - start_time:.2f}s"
                
                if success:
                    self.log_execution(
                        run_id, step_name, "SUCCESS", duration_str
                    )
                else:
                    self.log_execution(
                        run_id,
                        step_name,
                        "FAILED",
                        duration_str,
                        "Quality gate execution failure.",
                    )
                    logger.error(f"Pipeline stopped early at: {step_name}")
                    break
                    
        except Exception as e:
            logger.critical(f"Unhandled critical crash sequence: {e}")
