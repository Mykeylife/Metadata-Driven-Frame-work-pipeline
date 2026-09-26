import logging
import os
import sys
import uuid
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from typing import Any, Optional

# Import custom types and configuration vectors
from models import PipelineExecutionError, PipelineRun
from pipeline.config import get_db_path
from pipeline.dag_runner import DAGRunner

# 1. Establish file workspace directories for localized logging assets
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE_PATH = os.path.join(LOG_DIR, "pipeline_orchestrator.log")

# 2. Build explicit rotating log handler settings (5MB limits, rotating 3 logs maximum)
file_handler = RotatingFileHandler(
    LOG_FILE_PATH, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
)
console_handler = logging.StreamHandler(sys.stdout)

# Configure structured unified string format mapping rules
log_formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
file_handler.setFormatter(log_formatter)
console_handler.setFormatter(log_formatter)

# Initialize master platform core logger properties
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

logger = logging.getLogger("pipeline.orchestrator")


class PipelineOrchestrator:

    def __init__(
        self, db_path: Optional[str] = None, db_conn: Optional[Any] = None
    ) -> None:
        self.db_path = db_path if db_path is not None else get_db_path()
        self._test_conn = db_conn

    def _get_connection(self) -> sqlite3.Connection:
        if self._test_conn is not None:
            return self._test_conn
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def run_pipeline(self, run_id: str, pipeline_name: str) -> PipelineRun:
        """Runs the orchestration engine by checking statuses and processing tasks."""
        current_run = PipelineRun(
            run_id=run_id,
            pipeline_name=pipeline_name,
            status="RUNNING",
            started_at=datetime.now(timezone.utc),
        )
        
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pipeline_metadata (
                    step_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    step_name TEXT NOT NULL UNIQUE,
                    target_table TEXT NOT NULL,
                    execution_order INTEGER NOT NULL,
                    is_active INTEGER DEFAULT 1
                );
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pipeline_execution_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    step_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    execution_time TEXT NOT NULL,
                    peak_memory_kb INTEGER DEFAULT 0,
                    cpu_time_seconds REAL DEFAULT 0.0,
                    error_message TEXT
                );
            """)

            cursor.execute(
                "SELECT is_active FROM pipeline_metadata "
                "WHERE is_active = 1 LIMIT 1;"
            )
            if not cursor.fetchone():
                raise PipelineExecutionError(
                    "Pipeline orchestration sequence layer is empty or inactive."
                )

            cursor.execute("""
                INSERT INTO pipeline_execution_logs 
                (run_id, step_name, status, execution_time, error_message)
                VALUES (?, ?, ?, ?, ?)
            """, (current_run.run_id, pipeline_name, current_run.status, "0.00s", None))
            conn.commit()
            
            dag_runner = DAGRunner(db_path=self.db_path)
            if self._test_conn is not None:
                dag_runner._get_db_connection = self._get_connection

            dag_runner.run_pipeline()
            
            current_run.status = "SUCCESS"
            current_run.ended_at = datetime.now(timezone.utc)
            
            cursor.execute("""
                UPDATE pipeline_execution_logs 
                SET status = ?, error_message = ? 
                WHERE run_id = ? AND step_name = ?
            """, (current_run.status, f"Completed at {current_run.ended_at.isoformat()}", current_run.run_id, pipeline_name))
            conn.commit()
            
            return current_run
            
        except sqlite3.Error as e:
            raise PipelineExecutionError(f"Transaction failure: {str(e)}") from e
        finally:
            if self._test_conn is None:
                conn.close()

    def validate_execution_logs(self, run_id: str) -> None:
        """Verifies clean row insertion metrics post-run."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT run_id FROM pipeline_execution_logs WHERE run_id = ?;",
                (run_id,),
            )
            if not cursor.fetchone():
                raise PipelineExecutionError(f"Validation failed for {run_id}")
        finally:
            if self._test_conn is None:
                conn.close()


def run_pipeline(
    run_id: str,
    pipeline_name: str,
    db_path: Optional[str] = None,
    db_conn: Optional[Any] = None,
) -> PipelineRun:
    """Maintains clean module-level entry for script handles."""
    orchestrator = PipelineOrchestrator(db_path=db_path, db_conn=db_conn)
    return orchestrator.run_pipeline(run_id, pipeline_name)
