import sqlite3
from unittest.mock import patch, MagicMock
import pytest

# Dynamically patch configuration targets before loading to prevent layout path collisions
with patch("pipeline.config.get_db_path", return_value=":memory:"):
    try:
        from pipeline.dag_runner import DAGRunner
    except ImportError:
        from dag_runner import DAGRunner


class SafeTestConnection(sqlite3.Connection):
    """An isolated connection wrapper that blocks close signals to keep the in-memory test database open."""

    def close(self):
        pass  # Prevent runtime loops from closing the shared test fixture database early


@pytest.fixture
def clean_db_conn():
    """Provides a fresh, perfectly structured in-memory SQLite database for test insulation."""
    # Create the connection using our safe test subclass wrapper
    conn = sqlite3.connect(":memory:", factory=SafeTestConnection)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Build the production metadata control schemas
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

    # 2. Build the primary data-plane target tables required by DataQualityValidator structures
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

    # Finally, tear down and perform the real connection closure cleanly
    super(SafeTestConnection, conn).close()


def test_dag_runner_initialization():
    """Verifies that the runner initializes parameters correctly."""
    runner = DAGRunner(pipeline_name="Ingestion-Engine-Validation")
    assert runner.pipeline_name == "Ingestion-Engine-Validation"
    assert runner.status == "PENDING"


def test_dag_runner_successful_execution_loop(clean_db_conn):
    """Ensures the DAG execution engine walks through active transformations smoothly with valid data."""
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

    # Target the internal framework sub-logger configuration directly
    with patch("sqlite3.connect", return_value=clean_db_conn), patch(
        "pipeline.dag_runner.logger.info"
    ) as mock_logger:

        runner.run()

        # Verify status updates correctly on full lifecycle completion
        assert runner.status == "SUCCESS"
        mock_logger.assert_any_call("DAG step execution completed cleanly.")

        # Pull calculated state structures out to verify business analytical accuracy
        cursor.execute(
            "SELECT metric_value FROM summary_metrics WHERE metric_name = 'max_username_length';"
        )
        metric_row = cursor.fetchone()
        assert metric_row is not None
        assert (
            metric_row["metric_value"] == "11"
        )  # "alice_green" is 11 characters long


def test_dag_runner_skips_invalid_corrupted_rows(clean_db_conn):
    """Verifies that individual row validations gracefully drop corrupted records without breaking the run."""
    cursor = clean_db_conn.cursor()
    cursor.execute(
        "INSERT INTO pipeline_metadata (step_name, target_table, execution_order, is_active) VALUES (?, ?, ?, ?);",
        ("Aggregate Analytics Metrics", "summary_metrics", 10, 1),
    )
    # Seed one valid user and two corrupted records (null/empty strings) to evaluate the validator gating loop
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
        # Confirm that the data-quality gating messages were actively triggered
        mock_warn.assert_any_call(
            "Skipping individual corrupted data record inside staging sweep."
        )

        # Ensure KPIs are *only* recorded for the single clean user payload
        cursor.execute("SELECT COUNT(*) as count FROM analytics_kpis;")
        assert cursor.fetchone()["count"] == 1


def test_dag_runner_halts_if_all_rows_fail_validation(clean_db_conn):
    """Ensures that if all staging rows are completely corrupted, the step skips calculations gracefully."""
    cursor = clean_db_conn.cursor()
    cursor.execute(
# Change this line:
mock_warn.assert_any_call("No valid rows passed the data quality threshold for calculations.")

# To this (adding the 's' to thresholds):
mock_warn.assert_any_call("No valid rows passed the data quality thresholds for calculations.")
        "INSERT INTO pipeline_metadata (step_name, target_table, execution_order, is_active) VALUES (?, ?, ?, ?);",
        ("Aggregate Analytics Metrics", "summary_metrics", 10, 1),
    )
    cursor.execute(
        "INSERT INTO staging_users (id, username) VALUES (?, ?);", (1, "   ")
    )  # Spaces get trimmed and caught by validator
    clean_db_conn.commit()

    runner = DAGRunner(pipeline_name="All-Corrupted-Payload-Validation")

    with patch("sqlite3.connect", return_value=clean_db_conn), patch(
        "pipeline.dag_runner.logger.warning"
    ) as mock_warn:

        runner.run()

        assert runner.status == "SUCCESS"
        mock_warn.assert_any_call(
            "No valid rows passed the data quality threshold for calculations."
        )


def test_dag_runner_aborts_on_failed_boot_schema(clean_db_conn):
    """Validates that a broken database schema terminates the entire pipeline immediately at boot."""
    # Force a failure by dropping a core table required by the DataQualityValidator expectations
    cursor = clean_db_conn.cursor()
    # Temporarily drop safety locks to clear schema tables cleanly
    cursor.execute("DROP TABLE analytics_kpis;")
    clean_db_conn.commit()

    runner = DAGRunner(pipeline_name="Schema-Failure-Validation")

    with patch("sqlite3.connect", return_value=clean_db_conn), patch(
        "pipeline.dag_runner.logger.error"
    ) as mock_error:

        runner.run()

        # Pipeline must transition to FAILED instantly without querying steps
        assert runner.status == "FAILED"
        mock_error.assert_any_call(
            "Database boot schema validation failed. Halting runtime execution loop."
        )


def test_dag_runner_handles_empty_metadata_steps(clean_db_conn):
    """Validates that the runner transitions to an optimized SKIPPED state if no tasks match."""
    runner = DAGRunner(pipeline_name="Empty-Metadata-Context-Validation")

    with patch("sqlite3.connect", return_value=clean_db_conn), patch(
        "pipeline.dag_runner.logger.warning"
    ) as mock_logger:

        runner.run()

        assert runner.status == "SKIPPED"
        mock_logger.assert_any_call(
            "No operational steps registered for execution context."
        )


def test_dag_runner_safety_barrier_empty_staging_users(clean_db_conn):
    """Ensures the pipeline halts if an active step targets staging_users but the table has zero records."""
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
