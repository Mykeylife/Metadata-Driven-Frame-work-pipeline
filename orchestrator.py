import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

# Import custom types and configuration vectors
from models import PipelineExecutionError, PipelineRun
from pipeline.config import get_db_path
from pipeline.dag_runner import DAGRunner


class PipelineOrchestrator:

    def __init__(self, db_path: Optional[str] = None, db_conn: Optional[Any] = None) -> None:
        # Prioritize explicit paths, falling back to central config parameters
        self.db_path = db_path if db_path is not None else get_db_path()
        self._test_conn = db_conn

    def _get_connection(self) -> sqlite3.Connection:
        if self._test_conn is not None:
            return self._test_conn
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def run_pipeline(self, run_id: str, pipeline_name: str) -> PipelineRun:
        """Runs the orchestration engine by checking statuses and processing tasks via the DAG runner."""
        current_run = PipelineRun(
            run_id=run_id,
            pipeline_name=pipeline_name,
            status="RUNNING",
            started_at=datetime.now(timezone.utc)
        )
        
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Enforce centralized sequence and tracking tables
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
                    error_message TEXT
                );
            """)

            # Validation Gate: Ensure there is at least one active task mapped in our system
            cursor.execute("SELECT is_active FROM pipeline_metadata WHERE is_active = 1 LIMIT 1;")
            active_task = cursor.fetchone()
            
            if not active_task:
                # If there are no active tasks configured, we block processing cycles
                raise PipelineExecutionError(f"Pipeline orchestration sequence tracking layer is currently empty or inactive.")

            # Append the initialization footprint directly to the telemetries table
            cursor.execute("""
                INSERT INTO pipeline_execution_logs (run_id, step_name, status, execution_time, error_message)
                VALUES (?, ?, ?, ?, ?)
            """, (current_run.run_id, pipeline_name, current_run.status, "0.00s", None))
            conn.commit()
            
            # Instantiate DAG execution routines to handle task matrices
            dag_runner = DAGRunner(db_path=self.db_path)
            # Override connection if running under an active test runner environment setup
            if self._test_conn is not None:
                dag_runner._get_db_connection = lambda: self._get_connection()

            # Execute the comprehensive sequential processing loops
            dag_runner.run_pipeline()
            
            # Update the parent run state upon a successful execution sweep
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
            raise PipelineExecutionError(f"Database transaction failure: {str(e)}") from e
        finally:
            if self._test_conn is None:
                conn.close()

    def validate_execution_logs(self, run_id: str) -> None:
        """Verifies clean row insertion metrics post-run."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT run_id FROM pipeline_execution_logs WHERE run_id = ?", (run_id,))
            if not cursor.fetchone():
                raise PipelineExecutionError(f"Validation failed for run_id {run_id}")
        finally:
            if self._test_conn is None:
                conn.close()


def run_pipeline(run_id: str, pipeline_name: str, db_path: Optional[str] = None, db_conn: Optional[Any] = None) -> PipelineRun:
    """Maintains clean module-level entry for simple script execution handles."""
    orchestrator = PipelineOrchestrator(db_path=db_path, db_conn=db_conn)
    return orchestrator.run_pipeline(run_id, pipeline_name)
