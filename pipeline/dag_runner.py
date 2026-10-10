import os
import time
import uuid
import logging
import sqlite3
import resource
from typing import Optional
from pipeline.config import get_db_path
from pipeline.validators import DataQualityValidator

# Configure production logging layout
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("dag_runner")


class AuditStoreManager:
    """Handles atomic writes to the centralized local audit database table store."""

    @staticmethod
    def write_execution_log(
        db_path: str,
        run_id: str,
        step_name: str,
        status: str,
        duration_ms: float,
        peak_mem_kb: int,
        cpu_time_sec: float,
        error_msg: Optional[str] = None
    ) -> None:
        """Atomically inserts automated pipeline operational metrics directly into SQLite."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO pipeline_execution_logs (
                    run_id, step_name, status, execution_time, peak_memory_kb, cpu_time_seconds, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?);
            """, (
                run_id,
                step_name,
                status,
                f"{duration_ms:.2f}ms",
                peak_mem_kb,
                cpu_time_sec,
                error_msg
            ))
            conn.commit()
            logger.info("Successfully recorded audit metrics row for step: '%s'", step_name)
        except Exception as e:
            logger.error("Failed to commit telemetry data to Audit Store: %s", str(e))
        finally:
            conn.close()


class DAGRunner:
    """Orchestrates data parsing, transformations, and KPI loops using metadata configuration matrices."""

    def __init__(self, pipeline_name: str) -> None:
        self.pipeline_name: str = pipeline_name
        self.status: str = "PENDING"
        self.db_path: str = get_db_path()
        # Create a unique runtime execution footprint tracking number for this run session
        self.run_id: str = str(uuid.uuid4())

    def run(self) -> None:
        """Executes the data lifecycle processing steps sorted by operational priority order."""
        logger.info("Starting ingestion lifecycle execution for: %s (Run ID: %s)", self.pipeline_name, self.run_id)
        self.status = "RUNNING"
        
        start_time = time.time()
        start_ru = resource.getrusage(resource.RUSAGE_SELF)
        
        error_message: Optional[str] = None
        has_steps: bool = False

        try:
            # 1. Initialize and execute boot-level atomic schema verification
            validator = DataQualityValidator()
            if not validator.validate_atomic_schema(self.db_path):
                error_message = "Database boot schema validation failed. Halting runtime execution loop."
                logger.error(error_message)
                self.status = "FAILED"
                
                # Log the boot validation initialization crash to the Audit Store
                AuditStoreManager.write_execution_log(
                    db_path=self.db_path,
                    run_id=self.run_id,
                    step_name="BOOT_SCHEMA_VALIDATION",
                    status="FAILED",
                    duration_ms=0.0,
                    peak_mem_kb=start_ru.ru_maxrss,
                    cpu_time_sec=0.0,
                    error_msg=error_message
                )
                return

            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 2. Fetch active data tasks matching execution rules
            cursor.execute("""
                SELECT step_id, step_name, target_table, execution_order 
                FROM pipeline_metadata 
                WHERE is_active = 1
                ORDER BY execution_order ASC;
            """)
            steps = cursor.fetchall()

            if not steps:
                logger.warning("No operational steps registered for execution context.")
                self.status = "SKIPPED"
                conn.close()
                
                # Log empty configuration scenario layout metrics safely
                AuditStoreManager.write_execution_log(
                    db_path=self.db_path,
                    run_id=self.run_id,
                    step_name="NO_ACTIVE_STEPS_DISCOVERED",
                    status="SKIPPED",
                    duration_ms=(time.time() - start_time) * 1000,
                    peak_mem_kb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                    cpu_time_sec=0.0,
                    error_msg="No active steps registered in pipeline_metadata table."
                )
                return

            has_steps = True

            # 3. Iterate through data worker layers dynamically
            for step in steps:
                step_id = step["step_id"]
                step_name = step["step_name"]
                target_table = step["target_table"]
                
                step_start_time = time.time()
                step_start_ru = resource.getrusage(resource.RUSAGE_SELF)
                step_status = "SUCCESS"
                step_error: Optional[str] = None

                logger.info("[Step %d] Initializing worker: %s -> Target: %s", step_id, step_name, target_table)

                try:
                    # Row-count safety validation barrier
                    if target_table == "staging_users":
                        cursor.execute("SELECT COUNT(*) as cnt FROM staging_users;")
                        row = cursor.fetchone()
                        if row and row["cnt"] == 0:
                            step_error = "Safety guard triggered: 'staging_users' is completely empty. Halting pipeline."
                            logger.error(step_error)
                            step_status = "FAILED"
                            self.status = "FAILED"
                            break

                    # 4. Complete actual extraction, analytical calculation, and transformation loops
                    if step_name == "Aggregate Analytics Metrics" or target_table == "summary_metrics":
                        cursor.execute("SELECT username FROM staging_users;")
                        users = cursor.fetchall()
                        
                        if users:
                            valid_users = []
                            for u in users:
                                row_dict = dict(u) if u else {}
                                if validator.validate_row_record("staging_users", row_dict):
                                    valid_users.append(u)
                                else:
                                    logger.warning("Skipping individual corrupted data record inside staging sweep.")

                            if not valid_users:
                                logger.warning("No valid rows passed the data quality threshold for calculations.")
                                step_status = "SKIPPED"
                                step_error = "No valid rows passed data quality gating parameters."
                                continue

                            max_len = max(len(u["username"]) for u in valid_users if u["username"])
                            
                            cursor.execute("""
                                INSERT INTO summary_metrics (metric_name, metric_value, calculated_at)
                                VALUES ('max_username_length', ?, datetime('now'));
                            """, (str(max_len),))
                            
                            for user in valid_users:
                                username = user["username"]
                                if username:
                                    cursor.execute("""
                                        INSERT INTO analytics_kpis (username, username_length, processed_at)
                                        VALUES (?, ?, datetime('now'));
                                    """, (username, len(username)))

                    logger.info("[Step %d] Executed successfully.", step_id)

                except Exception as step_ex:
                    step_status = "FAILED"
                    step_error = str(step_ex)
                    self.status = "FAILED"
                    logger.error("[Step %d] Critical loop failure: %s", step_id, step_error)
                    break
                
                finally:
                    # Document granular microsecond footprint per step row asynchronously into audit trail
                    step_end_time = time.time()
                    step_end_ru = resource.getrusage(resource.RUSAGE_SELF)
                    
                    step_duration_ms = (step_end_time - step_start_time) * 1000
                    step_cpu_time = (step_end_ru.ru_utime - start_ru.ru_utime) + (step_end_ru.ru_stime - start_ru.ru_stime)
                    
                    AuditStoreManager.write_execution_log(
                        db_path=self.db_path,
                        run_id=self.run_id,
                        step_name=step_name,
                        status=step_status,
                        duration_ms=step_duration_ms,
                        peak_mem_kb=step_end_ru.ru_maxrss,
                        cpu_time_sec=step_cpu_time,
                        error_msg=step_error
                    )

            if self.status != "FAILED":
                self.status = "SUCCESS"
                conn.commit()
                logger.info("DAG step execution completed cleanly.")

            conn.close()

        except Exception as e:
            self.status = "FAILED"
            error_message = str(e)
            logger.error("Fatal exception broken sequence execution loop: %s", error_message)
            raise e

