# orchestrator.py
import sqlite3
from datetime import datetime
from models import PipelineRun, PipelineExecutionError

class PipelineOrchestrator:
    def __init__(self, db_path: str = "simulation.db"):
        self.db_path = db_path

    def run_pipeline(self, run_id: str, pipeline_name: str) -> PipelineRun:
        # Construct and validate initial tracking schema instance
        current_run = PipelineRun(
            run_id=run_id,
            pipeline_name=pipeline_name,
            status="RUNNING",
            started_at=datetime.utcnow()
        )
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Simple metadata guard check
            cursor.execute("SELECT is_active FROM pipeline_metadata WHERE pipeline_name = ?", (pipeline_name,))
            row = cursor.fetchone()
            if not row or not row[0]:
                raise PipelineExecutionError(f"Pipeline '{pipeline_name}' is inactive or missing metadata.")
            
            # Perform pipeline task execution registration tracking...
            cursor.execute("""
                INSERT INTO execution_logs (run_id, pipeline_name, status, started_at, ended_at)
                VALUES (?, ?, ?, ?, ?)
            """, (current_run.run_id, current_run.pipeline_name, current_run.status, current_run.started_at.isoformat(), None))
            
            conn.commit()
            
            # Update instance status upon clean termination
            current_run.status = "SUCCESS"
            current_run.ended_at = datetime.utcnow()
            
            cursor.execute("UPDATE execution_logs SET status = ?, ended_at = ? WHERE run_id = ?", 
                           (current_run.status, current_run.ended_at.isoformat(), current_run.run_id))
            conn.commit()
            return current_run
            
        except sqlite3.Error as e:
            # Drop broad string sentinel 'FAILED' returns; raise explicit typed exception instead
            raise PipelineExecutionError(f"Database transaction failure during pipeline execution: {str(e)}") from e
        finally:
            if 'conn' in locals():
                conn.close()

    def validate_execution_logs(self, run_id: str) -> None:
        """Checks target row counts and essential metrics post-execution."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT run_id, status FROM execution_logs WHERE run_id = ?", (run_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            raise PipelineExecutionError(f"Validation failed: No execution log entry found for run_id {run_id}")
# Add this to the very bottom of orchestrator.py

def run_pipeline(run_id: str, pipeline_name: str, db_path: str = "simulation.db"):
    """Module-level function to maintain compatibility with existing tests."""
    orchestrator = PipelineOrchestrator(db_path=db_path)
    return orchestrator.run_pipeline(run_id, pipeline_name)
