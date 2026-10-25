"""Orchestrates metadata-driven pipelines via cleanly isolated transaction patterns with data governance."""

import hashlib
import json
import logging
import sqlite3
import time
import uuid

try:
    import resource
except ImportError:
    resource = None  # Handle non-Unix local debugging platforms safely

from . import kpi_calculator, repository
from .config import get_db_path
from .logging_config import JsonStructuredFormatter
from .validators import DataQualityValidator

# Explicit structured logger setup
handler = logging.StreamHandler()
handler.setFormatter(JsonStructuredFormatter())
logger = logging.getLogger("dag_runner")
logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False


class DAGRunner:
    """Orchestrates loop cycles using decoupled data management models with lineage tracking."""

    def __init__(self, pipeline_name: str) -> None:
        self.pipeline_name: str = pipeline_name
        self.status: str = "PENDING"
        self.db_path: str = get_db_path()
        self.run_id: str = str(uuid.uuid4())

    def _generate_lineage_hash(self, rows: list) -> str:
        """Generates a deterministic cryptographic hash representing data state provenance."""
        if not rows:
            return hashlib.sha256(b"empty_dataset").hexdigest()

        # Serialize and sort rows to ensure deterministic hashing
        serialized_data = json.dumps([dict(r) for r in rows], sort_keys=True, default=str)
        return hashlib.sha256(serialized_data.encode("utf-8")).hexdigest()

    def run(self) -> None:
        """Executes processing phases sequentially with strict gating and governance telemetry."""
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

                # Baseline telemetry initialization
                repository.log_pipeline_telemetry(
                    cursor,
                    self.run_id,
                    step_name,
                    "RUNNING",
                    licensing_governance="MIT-Data-Asset-v1",
                )

                # Variables to hold calculated governance metrics
                lineage_hash = None
                quality_score = 1.0

                # Row-count safety validation barrier
                if target_table == "staging_users":
                    row_count = repository.check_table_row_count(cursor, "staging_users")
                    if row_count == 0:
                        error_msg = "Safety guard triggered: 'staging_users' is completely empty. Halting pipeline."
                        logger.error(error_msg)
                        repository.log_pipeline_telemetry(
                            cursor,
                            self.run_id,
                            step_name,
                            "FAILED",
                            error_message=error_msg,
                            quality_score=0.0,
                        )
                        self.status = "FAILED"
                        break

                # Calculation & Transformation Phase
                if step_name == "Aggregate Analytics Metrics" or target_table == "summary_metrics":
                    raw_users = repository.fetch_staging_usernames(cursor)

                    # 1. Compute Cryptographic Lineage Hash for Audit Trail
                    lineage_hash = self._generate_lineage_hash(raw_users)

                    if raw_users:
                        # 2. Compute Quality Score based on valid records passing the validation threshold
                        total_rows = len(raw_users)
                        valid_records = []
                        for u in raw_users:
                            row_dict = dict(u) if hasattr(u, "keys") else {"username": str(u)}
                            if validator.validate_row_record("staging_users", row_dict):
                                valid_records.append(u)

                        quality_score = round(len(valid_records) / total_rows, 4)

                        # Process metrics using your underlying KPI engine
                        kpi_calculator.process_aggregate_metrics(cursor, raw_users, validator)

                # Commit telemetry alongside data governance metadata
                repository.log_pipeline_telemetry(
                    cursor,
                    self.run_id,
                    step_name,
                    "SUCCESS",
                    data_lineage_hash=lineage_hash,
                    quality_score=quality_score,
                    licensing_governance="MIT-Data-Asset-v1",
                )
                logger.info(f"[Step {step_id}] Executed successfully with Quality Score: {quality_score}")

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

            if resource and start_ru:
                end_ru = resource.getrusage(resource.RUSAGE_SELF)
                cpu_time = (end_ru.ru_utime - start_ru.ru_utime) + (end_ru.ru_stime - start_ru.ru_stime)
                peak_memory = end_ru.ru_maxrss
            else:
                cpu_time, peak_memory = 0.0, 0

            logger.info(
                f"Pipeline metrics tracked -> Duration: {duration:.4f}s | CPU Time: {cpu_time:.4f}s | Peak Memory: {peak_memory} KB"
            )


if __name__ == "__main__":
    runner = DAGRunner(pipeline_name="Production-Ingestion-Flow")
    runner.run()
