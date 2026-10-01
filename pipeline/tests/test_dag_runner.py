import os
import time
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


class DAGRunner:
    """Orchestrates data parsing, transformations, and KPI loops using metadata configuration matrices."""

    def __init__(self, pipeline_name: str) -> None:
        self.pipeline_name: str = pipeline_name
        self.status: str = "PENDING"
        self.db_path: str = get_db_path()

    def run(self) -> None:
        """Executes the data lifecycle processing steps sorted by operational priority order."""
        logger.info("Starting ingestion lifecycle execution for: %s", self.pipeline_name)
        self.status = "RUNNING"
        
        start_time = time.time()
        start_ru = resource.getrusage(resource.RUSAGE_SELF)

        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 1. Fetch active data tasks matching execution rules
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
                return

            validator = DataQualityValidator()

            # 2. Iterate through data worker layers dynamically
            for step in steps:
                step_id = step["step_id"]
                step_name = step["step_name"]
                target_table = step["target_table"]

                logger.info("[Step %d] Initializing worker: %s -> Target: %s", step_id, step_name, target_table)

                # Row-count safety validation barrier
                if target_table == "staging_users":
                    cursor.execute("SELECT COUNT(*) as cnt FROM staging_users;")
                    row = cursor.fetchone()
                    if row and row["cnt"] == 0:
                        logger.error("Safety guard triggered: 'staging_users' is completely empty. Halting pipeline.")
                        self.status = "FAILED"
                        break

                # 3. Complete actual extraction, analytical calculation, and transformation loops
                if step_name == "Aggregate Analytics Metrics" or target_table == "summary_metrics":
                    # Compute analytical metrics from production datasets
                    cursor.execute("SELECT username FROM staging_users;")
                    users = cursor.fetchall()
                    
                    if users:
                        max_len = max(len(u["username"]) for u in users if u["username"])
                        
                        # Insert computed KPIs directly into data stores safely
                        cursor.execute("""
                            INSERT INTO summary_metrics (metric_name, metric_value, calculated_at)
                            VALUES ('max_username_length', ?, datetime('now'));
                        """, (str(max_len),))
                        
                        # Calculate and store individual customer metric boundaries
                        for user in users:
                            username = user["username"]
                            if username:
                                cursor.execute("""
                                    INSERT INTO analytics_kpis (username, username_length, processed_at)
                                    VALUES (?, ?, datetime('now'));
                                """, (username, len(username)))

                logger.info("[Step %d] Executed successfully.", step_id)

            if self.status != "FAILED":
                self.status = "SUCCESS"
                conn.commit()
                logger.info("DAG step execution completed cleanly.")

            conn.close()

        except Exception as e:
            self.status = "FAILED"
            logger.error("Critical failure during DAG loop execution: %s", str(e))
            raise e

        finally:
            # 4. Measure biometrics tracking footprint
            end_time = time.time()
            end_ru = resource.getrusage(resource.RUSAGE_SELF)
            
            duration = end_time - start_time
            cpu_time = (end_ru.ru_utime - start_ru.ru_utime) + (end_ru.ru_stime - start_ru.ru_stime)
            peak_memory = end_ru.ru_maxrss  # Measured in kilobytes

            logger.info("Pipeline metrics tracked -> Duration: %.4fs | CPU Time: %.4fs | Peak Memory: %d KB", 
                        duration, cpu_time, peak_memory)


if __name__ == "__main__":
    runner = DAGRunner(pipeline_name="Production-Ingestion-Flow")
    runner.run()
