import sqlite3
import uuid
import logging
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("metadata_orchestrator")

class PipelineConfig(BaseModel):
    pipeline_id: str
    pipeline_name: str
    source_type: str
    target_path: str

class OrchestratorDB:
    def __init__(self, db_path: str = "metadata_control.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self) -> None:
        """Initializes tables locally if they do not exist yet."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Dynamic generation matching our sql schema definition
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS adf_pipelines (
                    pipeline_id TEXT PRIMARY KEY, pipeline_name TEXT NOT NULL,
                    source_type TEXT NOT NULL, target_path TEXT NOT NULL, is_active INTEGER DEFAULT 1
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS adf_execution_logs (
                    run_id TEXT PRIMARY KEY, pipeline_id TEXT NOT NULL, status TEXT NOT NULL,
                    started_at TEXT NOT NULL, completed_at TEXT, records_processed INTEGER DEFAULT 0, error_message TEXT
                )
            """)
            # Auto-seed baseline configuration mapping rule if table empty
            cursor.execute("SELECT COUNT(*) FROM adf_pipelines")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO adf_pipelines (pipeline_id, pipeline_name, source_type, target_path)
                    VALUES ('PL_SM_001', 'Social_Media_API_Ingestion', 'API', '/data/output/social_media/')
                """)
            conn.commit()

    def get_pipeline_config(self, pipeline_id: str) -> Optional[PipelineConfig]:
        """Fetches active metadata rules configuration directly out of SQLite memory framework."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM adf_pipelines WHERE pipeline_id = ? AND is_active = 1", (pipeline_id,))
            row = cursor.fetchone()
            if row:
                return PipelineConfig(
                    pipeline_id=row["pipeline_id"],
                    pipeline_name=row["pipeline_name"],
                    source_type=row["source_type"],
                    target_path=row["target_path"]
                )
        return None

    def start_log(self, pipeline_id: str) -> str:
        run_id = str(uuid.uuid4())
        with sqlite3.connect(self.db_path) as conn:
            conn.cursor().execute(
                "INSERT INTO adf_execution_logs (run_id, pipeline_id, status, started_at) VALUES (?, ?, 'RUNNING', ?)",
                (run_id, pipeline_id, datetime.utcnow().isoformat())
            )
            conn.commit()
        return run_id

    def end_log(self, run_id: str, status: str, records: int = 0, error: str = None) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.cursor().execute(
                "UPDATE adf_execution_logs SET status = ?, completed_at = ?, records_processed = ?, error_message = ? WHERE run_id = ?",
                (status, datetime.utcnow().isoformat(), records, error, run_id)
            )
            conn.commit()

def run_orchestration(pipeline_id: str) -> str:
    """Core runtime managing tracking operations through local SQLite validation structures."""
    db = OrchestratorDB()
    config = db.get_pipeline_config(pipeline_id)
    
    if not config:
        logger.error(f"Execution rejected: Pipeline configuration ID '{pipeline_id}' not found or inactive.")
        return "Rejected"

    run_id = db.start_log(pipeline_id)
    logger.info(f"Initialized Run ID: {run_id} for Pipeline: {config.pipeline_name}")

    try:
        # Mock execution logic (e.g., Calling your Social Media API endpoints, transforming schema parameters)
        logger.info(f"Extracting target parameters via source engine: {config.source_type}...")
        
        # Complete transaction record successfully
        db.end_log(run_id=run_id, status="SUCCESS", records=150)
        logger.info(f"Pipeline Run {run_id} finalized successfully.")
        return "Success"
        
    except Exception as exc:
        db.end_log(run_id=run_id, status="FAILED", error=str(exc))
        logger.error(f"Pipeline Run {run_id} failed: {str(exc)}")
        return "Failure"
