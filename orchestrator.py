# orchestrator.py
import sqlite3
from datetime import datetime
from models import PipelineRun, PipelineExecutionError

class PipelineOrchestrator:
    def __init__(self, db_path: str = "simulation.db", db_conn=None):
        self.db_path = db_path
        self._test_conn = db_conn

    def _get_connection(self):
        if self._test_conn is not None:
            return self._test_conn
        return sqlite3.connect(self.db_path)

    def run_pipeline(self, run_id: str, pipeline_name: str) -> PipelineRun:
        current_run = PipelineRun(
            run_id=run_id,
            pipeline_name=pipeline_name,
            status="RUNNING",
            started_at=datetime.utcnow()
        )
        
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Enforce clean infrastructure
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pipeline_metadata (
                    pipeline_name TEXT PRIMARY KEY,
                    is_active INTEGER DEFAULT 1
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS execution_logs (
                    run_id TEXT PRIMARY KEY,
                    pipeline_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    ended_at TEXT
                )
            """)

            cursor.execute("SELECT is_active FROM pipeline_metadata WHERE pipeline_name = ?", (pipeline_name,))
            row = cursor.fetchone()
            if row and row[0] == 0:
                raise PipelineExecutionError(f"Pipeline '{pipeline_name}' is inactive.")

            cursor.execute("""
                INSERT INTO execution_logs (run_id, pipeline_name, status, started_at, ended_at)
                VALUES (?, ?, ?, ?, ?)
            """, (current_run.run_id, current_run.pipeline_name, current_run.status, current_run.started_at.isoformat(), None))
            
            conn.commit()
            
            current_run.status = "SUCCESS"
            current_run.ended_at = datetime.utcnow()
            
            cursor.execute("UPDATE execution_logs SET status = ?, ended_at = ? WHERE run_id = ?", 
                           (current_run.status, current_run.ended_at.isoformat(), current_run.run_id))
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
            cursor.execute("SELECT run_id FROM execution_logs WHERE run_id = ?", (run_id,))
            if not cursor.fetchone():
                raise PipelineExecutionError(f"Validation failed for run_id {run_id}")
        finally:
            if self._test_conn is None:
                conn.close()

def run_pipeline(run_id: str, pipeline_name: str, db_path: str = "simulation.db", db_conn=None):
    """Maintains clean module-level entry for simple script execution handles."""
    orchestrator = PipelineOrchestrator(db_path=db_path, db_conn=db_conn)
    return orchestrator.run_pipeline(run_id, pipeline_name)
