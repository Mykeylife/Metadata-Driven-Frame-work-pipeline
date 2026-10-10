"""Orchestrates metadata-driven pipelines via cleanly isolated transaction patterns."""

import os
import time
import logging
import sqlite3
import uuid
try:
    import resource
except ImportError:
    resource = None  # Handle non-Unix local debugging platforms safely

from pipeline.config import get_db_path
from pipeline.validators import DataQualityValidator
from pipeline.logging_config import JsonStructuredFormatter
from pipeline import repository
from pipeline import kpi_calculator

# Explicit structured logger setup
handler = logging.StreamHandler()
handler.setFormatter(JsonStructuredFormatter())
logger = logging.getLogger("dag_runner")
logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False


class DAGRunner:
    """Orchestrates loop cycles using decoupled data management models."""

    def __init__(self, pipeline_name: str) -> None:
        self.pipeline_name: str = pipeline_name
        self.status: str = "PENDING"
        self.db_path: str = get_db_path()
        self.run_id: str = str(uuid.uuid4())

    def run(self) -> None:
        """Executes processing phases sequentially with strict gating boundaries."""
        logger.info(f"Starting ingestion lifecycle execution for: {self.pipeline_name}")
        self.status = "RUNNING"
        
        start_time = time.time()
        start_ru = resource.getrusage(resource.RUSAGE_SELF) if resource else None

        try:
            validator = DataQualityValidator()
            if not validator.validate_atomic_schema(self.db_path):
                logger.error("Database boot schema validation failed. Halting runtime execution loop.")
                self.status = "FAILED"
                return

            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            steps = repository.fetch_active_metadata_steps(cursor)
            if not steps:
                logger.warning("No operational steps registered for execution context.")
                self.status = "SKIPPED"
                conn.close()
                return

            for step in steps:
                step_id = step["step_id"]
                step_name = step["step_name"]
                target_table = step["target_table"]

                logger.info(f"[Step {step_id}] Initializing worker: {step_name} -> Target: {target_table}")
                repository.log_pipeline_telemetry(cursor, self.run_id, step_name, "RUNNING")

                # Row-count safety validation barrier
                if target_table == "staging_users":
                    if repository.check_table_row_count(cursor, "staging_users") == 0:
                        error_msg = "Safety guard triggered: 'staging_users' is completely empty. Halting pipeline."
                        logger.error(error_msg)
                        repository.log_pipeline_telemetry(cursor, self.run_id, step_name, "FAILED", error_msg)
                        self.status = "FAILED"
                        break

                # Calculation phase
                if step_name == "Aggregate Analytics Metrics" or target_table == "summary_metrics":
                    users = repository.fetch_staging_usernames(cursor)
                    if users:
                        kpi_calculator.process_aggregate_metrics(cursor, users, validator)

                repository.log_pipeline_telemetry(cursor, self.run_id, step_name, "SUCCESS")
                logger.info(f"[Step {step_id}] Executed successfully.")

            if self.status != "FAILED":
                self.status = "SUCCESS"
                conn.commit()
                logger.info("DAG step execution completed cleanly.")

            conn.close()

        except Exception as e:
            self.status = "FAILED"
            logger.error(f"Critical failure during DAG loop execution: {str(e)}")
            raise e

        finally:
            end_time = time.time()
            duration = end_time - start_time
            
            # Extract footprints safely across system containers
            if resource and start_ru:
                end_ru = resource.getrusage(resource.RUSAGE_SELF)
                cpu_time = (end_ru.ru_utime - start_ru.ru_utime) + (end_ru.ru_stime - start_ru.ru_stime)
                peak_memory = end_ru.ru_maxrss
            else:
                cpu_time, peak_memory = 0.0, 0

            logger.info(f"Pipeline metrics tracked -> Duration: {duration:.4f}s | CPU Time: {cpu_time:.4f}s | Peak Memory: {peak_memory} KB")


if __name__ == "__main__":
    runner = DAGRunner(pipeline_name="Production-Ingestion-Flow")
    runner.run()
