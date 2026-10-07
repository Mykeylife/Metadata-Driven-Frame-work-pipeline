import sqlite3
from unittest.mock import MagicMock, patch
import pytest

with patch("pipeline.config.get_db_path", return_value=":memory:"):
    try:
        from pipeline.dag_runner import DAGRunner
    except ImportError:
        from dag_runner import DAGRunner

class SafeTestConnection(sqlite3.Connection):
    def close(self):
        pass

@pytest.fixture
def clean_db_conn():
    conn = sqlite3.connect(":memory:", factory=SafeTestConnection)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE pipeline_metadata (
            step_id INTEGER PRIMARY KEY AUTOINCREMENT,
            step_name TEXT NOT NULL,
            target_table TEXT NOT NULL,
            execution_order INTEGER NOT NULL,
            is_active INTEGER DEFAULT 1
        );
    """)
    cursor.execute("CREATE TABLE staging_users (id INTEGER PRIMARY KEY, username TEXT);")
    cursor.execute("CREATE TABLE analytics_kpis (kpi_id INTEGER PRIMARY KEY, username TEXT, username_length INTEGER, processed_at TEXT);")
    cursor.execute("CREATE TABLE summary_metrics (summary_id INTEGER PRIMARY KEY, metric_name TEXT, metric_value TEXT, calculated_at TEXT);")
    conn.commit()
    yield conn
    super(SafeTestConnection, conn).close()

def test_dag_runner_initialization():
    runner = DAGRunner(pipeline_name="Ingestion-Engine-Validation")
    assert runner.pipeline_name == "Ingestion-Engine-Validation"
    assert runner.status == "PENDING"

def test_dag_runner_successful_execution_loop(clean_db_conn):
    cursor = clean_db_conn.cursor()
    cursor.execute("INSERT INTO pipeline_metadata (step_name, target_table, execution_order, is_active) VALUES (?, ?, ?, ?);", ("Aggregate Analytics Metrics", "summary_metrics", 10, 1))
    cursor.executemany("INSERT INTO staging_users (id, username) VALUES (?, ?);", [(1, "alice_green"), (2, "bob_secure")])
    clean_db_conn.commit()
    runner = DAGRunner(pipeline_name="Ingestion-Engine-Validation")
    with patch("sqlite3.connect", return_value=clean_db_conn), patch("pipeline.dag_runner.logger.info") as mock_logger:
        runner.run()
        assert runner.status == "SUCCESS"
        mock_logger.assert_any_call("DAG step execution completed cleanly.")

def test_dag_runner_halts_if_all_rows_fail_validation(clean_db_conn):
    cursor = clean_db_conn.cursor()
    cursor.execute("INSERT INTO pipeline_metadata (step_name, target_table, execution_order, is_active) VALUES (?, ?, ?, ?);", ("Aggregate Analytics Metrics", "summary_metrics", 10, 1))
    cursor.execute("INSERT INTO staging_users (id, username) VALUES (?, ?);", (1, "   "))
    clean_db_conn.commit()
    runner = DAGRunner(pipeline_name="All-Corrupted-Payload-Validation")
    with patch("sqlite3.connect", return_value=clean_db_conn), patch("pipeline.dag_runner.logger.warning") as mock_warn:
        runner.run()
        assert runner.status == "SUCCESS"
        mock_warn.assert_any_call("No valid rows passed the data quality thresholds for calculations.")
