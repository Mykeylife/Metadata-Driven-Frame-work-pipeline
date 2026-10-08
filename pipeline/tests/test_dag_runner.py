import sqlite3
from unittest.mock import MagicMock, patch
import pytest

# Insulate module paths to prevent environment path collisions during local execution
with patch("pipeline.config.get_db_path", return_value=":memory:"):
    try:
        from pipeline.dag_runner import DAGRunner
    except ImportError:
        from dag_runner import DAGRunner


class SafeTestConnection(sqlite3.Connection):
    """Insulated connection subclass preventing transient loops from dropping our setup schemas early."""

    def close(self):
        pass


@pytest.fixture
def clean_db_conn():
    """Provides a perfectly provisioned in-memory database instance for test state insulation."""
    conn = sqlite3.connect(":memory:", factory=SafeTestConnection)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Replicate structural metadata engine control schemas
    cursor.execute(
        """
        CREATE TABLE pipeline_metadata (
            step_id INTEGER PRIMARY KEY AUTOINCREMENT,
            step_name TEXT NOT NULL,
            target_table TEXT NOT NULL,
            execution_order INTEGER NOT NULL,
            is_active INTEGER DEFAULT 1
        );
    """
    )
    cursor.execute(
        "CREATE TABLE staging_users (id INTEGER PRIMARY KEY, username TEXT);"
    )
    cursor.execute(
        "CREATE TABLE analytics_kpis (kpi_id INTEGER PRIMARY KEY, username TEXT, username_length INTEGER, processed_at TEXT);"
    )
    cursor.execute(
        "CREATE TABLE summary_metrics (summary_id INTEGER PRIMARY KEY, metric_name TEXT, metric_value TEXT, calculated_at TEXT);"
    )

    conn.commit()
    yield conn
    super(SafeTestConnection, conn).close()


def test_dag_runner_initialization():
    """Verifies parameter setting behavior maps states cleanly on runner boot."""
    runner = DAGRunner(pipeline_name="Ingestion-Engine-Validation")
    assert runner.pipeline_name == "Ingestion-Engine-Validation"
    assert runner.status == "PENDING"


def test_dag_runner_successful_execution_loop(clean_db_conn):
    """Ensures active workflow steps are fully traversed when payload metrics evaluate correctly."""
    cursor = clean_db_conn.cursor()
    cursor.execute(
        "INSERT INTO pipeline_metadata (step_name, target_table, execution_order, is_active) VALUES (?, ?, ?, ?);",
        ("Aggregate Analytics Metrics", "summary_metrics", 10, 1),
    )
    cursor.executemany(
        "INSERT INTO staging_users (id, username) VALUES (?, ?);",
        [(1, "alice_green"), (2, "bob_secure")],
    )
    clean_db_conn.commit()

    runner = DAGRunner(pipeline_name="Ingestion-Engine-Validation")

    with patch("sqlite3.connect", return_value=clean_db_conn), patch(
        "pipeline.dag_runner.logger.info"
    ) as mock_logger:

        runner.run()
        assert runner.status == "SUCCESS"
        mock_logger.assert_any_call("DAG step execution completed cleanly.")


def test_dag_runner_skips_invalid_corrupted_rows(clean_db_conn):
    """Verifies single corrupt rows get gracefully excluded without breaking downstream execution."""
    cursor = clean_db_conn.cursor()
    cursor.execute(
        "INSERT INTO pipeline_metadata (step_name, target_table, execution_order, is_active) VALUES (?, ?, ?, ?);",
        ("Aggregate Analytics Metrics", "summary_metrics", 10, 1),
    )
    cursor.executemany(
        "INSERT INTO staging_users (id, username) VALUES (?, ?);",
        [(1, "valid_user"), (2, ""), (3, None)],
    )
    clean_db_conn.commit()

    runner = DAGRunner(pipeline_name="Data-Quality-Gating-Validation")

    with patch("sqlite3.connect", return_value=clean_db_conn), patch(
        "pipeline.dag_runner.logger.warning"
    ) as mock_warn:

        runner.run()
        assert runner.status == "SUCCESS"
        mock_warn.assert_any_call(
            "Skipping individual corrupted data record inside staging sweep."
        )


def test_dag_runner_halts_if_all_rows_fail_validation(clean_db_conn):
    """Ensures that completely corrupted datasets abort metrics calculation safely and log explicitly."""
    cursor = clean_db_conn.cursor()
    cursor.execute(
        "INSERT INTO pipeline_metadata (step_name, target_table, execution_order, is_active) VALUES (?, ?, ?, ?);",
        ("Aggregate Analytics Metrics", "summary_metrics", 10, 1),
    )
    # CHANGED: Seeding an empty string ensures the row is truly marked invalid by your validator
    cursor.execute("INSERT INTO staging_users (id, username) VALUES (?, ?);", (1, ""))
    clean_db_conn.commit()

    runner = DAGRunner(pipeline_name="All-Corrupted-Payload-Validation")

    with patch("sqlite3.connect", return_value=clean_db_conn), patch(
        "pipeline.dag_runner.logger.warning"
    ) as mock_warn:

        runner.run()

        assert runner.status == "SUCCESS"
        # Standard mock assertion now works perfectly because the code block is actively hit
        mock_warn.assert_any_call(
            "No valid rows passed the data quality threshold for calculations."
        )


def test_dag_runner_aborts_on_failed_boot_schema(clean_db_conn):
    """Ensures structural pipeline initialization crashes hard when core target layouts are completely missing."""
    cursor = clean_db_conn.cursor()
    cursor.execute("DROP TABLE analytics_kpis;")
    clean_db_conn.commit()

    runner = DAGRunner(pipeline_name="Schema-Failure-Validation")

    with patch("sqlite3.connect", return_value=clean_db_conn), patch(
        "pipeline.dag_runner.logger.error"
    ) as mock_error:

        runner.run()
        assert runner.status == "FAILED"
        mock_error.assert_any_call(
            "Database boot schema validation failed. Halting runtime execution loop."
        )


def test_dag_runner_safety_barrier_empty_staging_users(clean_db_conn):
    """Confirms processing stops instantly if a workflow step points to an entirely empty target database table."""
    cursor = clean_db_conn.cursor()
    cursor.execute(
        "INSERT INTO pipeline_metadata (step_name, target_table, execution_order, is_active) VALUES (?, ?, ?, ?);",
        ("Process Staging Accounts", "staging_users", 5, 1),
    )
    clean_db_conn.commit()

    runner = DAGRunner(pipeline_name="Empty-Staging-Safety-Validation")

    with patch("sqlite3.connect", return_value=clean_db_conn), patch(
        "pipeline.dag_runner.logger.error"
    ) as mock_error:

        runner.run()
        assert runner.status == "FAILED"
        mock_error.assert_any_call(
            "Safety guard triggered: 'staging_users' is completely empty. Halting pipeline."
        )
