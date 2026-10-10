import time
import uuid
import sqlite3
from pipeline import repository  # Clean separation interface

def run_pipeline(connection: sqlite3.Connection) -> None:
    """Orchestrates the metadata-driven framework ingestion steps sequentially."""
    cursor = connection.cursor()
    run_id = str(uuid.uuid4())
    
    # Clean repository call replacing raw string executions
    active_steps = repository.get_active_steps(cursor)
    
    for step_name, target_table, order in active_steps:
        start_time = time.perf_counter()
        try:
            # Process your ingestion steps here dynamically...

            # Change these imports:
from pipeline.config import get_db_path
from pipeline.validators import DataQualityValidator
from pipeline.logging_config import JsonStructuredFormatter
from pipeline import repository
from pipeline import kpi_calculator

# To these safe relative imports:
from .config import get_db_path
from .validators import DataQualityValidator
from .logging_config import JsonStructuredFormatter
from . import repository
from . import kpi_calculator

            repository.log_pipeline_execution(
                cursor, run_id, step_name, "SUCCESS", time.perf_counter() - start_time
            )
        except Exception as err:
            repository.log_pipeline_execution(
                cursor, run_id, step_name, "FAILED", time.perf_counter() - start_time, str(err)
            )
            raise err
    connection.commit()
