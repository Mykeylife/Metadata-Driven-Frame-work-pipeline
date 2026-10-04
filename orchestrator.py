import logging
import sqlite3
import sys
from typing import TYPE_CHECKING, List, Tuple

# Prevent Mypy from identifying duplicate definitions during structural analysis
if TYPE_CHECKING:
    from pipeline.config import get_db_path
    from pipeline.dag_runner import DAGRunner
else:
    try:
        # Handles execution context when run from the repository root directory
        from pipeline.config import get_db_path
        from pipeline.dag_runner import DAGRunner
    except ModuleNotFoundError:
        # Handles direct execution or inner package context during absolute paths
        from config import get_db_path
        from dag_runner import DAGRunner

# Configure structured production-ready terminal logging framework
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("pipeline_orchestrator")

DB_PATH = get_db_path()

def fetch_active_steps() -> List[Tuple[int, str, str, int]]:
    """Retrieves all active configuration steps sorted by execution priority order."""
    logger.info("Connecting to metadata infrastructure database at '%s'...", DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    query = """
        SELECT step_id, step_name, target_table, execution_order 
        FROM pipeline_metadata 
        WHERE is_active = 1
        ORDER BY execution_order ASC;
    """
    cursor.execute(query)
    steps = cursor.fetchall()
    conn.close()
    
    logger.info("Successfully discovered %d active ingestion tasks.", len(steps))
    return steps

def execute_pipeline() -> None:
    """Orchestrates the sequence flow of data ingestion steps based on control tables."""
    logger.info("Initializing metadata-driven orchestrator engine run...")
    active_steps = fetch_active_steps()
    
    if not active_steps:
        logger.warning("No active steps found in control tables. Exiting engine flow safely.")
        return

    # Triggering the dynamic DAGRunner to parse, validate, and compute analytical data KPIs live
    try:
        logger.info("Active metadata steps validated. Instantiating DAG runner execution loop...")
        runner = DAGRunner(pipeline_name="Production-Orchestrated-Ingestion-Flow")
        runner.run()
        
        if runner.status == "SUCCESS":
            logger.info("Metadata-driven orchestrator engine executed all tasks successfully! 🚀")
        elif runner.status == "SKIPPED":
            logger.warning("DAG runner completed execution with a SKIPPED status flag.")
        else:
            raise RuntimeError(f"DAG runner terminated with an unexpected status: {runner.status}")
            
    except Exception as e:
        logger.error("Critical orchestration failure detected: %s", str(e))
        raise

if __name__ == "__main__":
    execute_pipeline()
