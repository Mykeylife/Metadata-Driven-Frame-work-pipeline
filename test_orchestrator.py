import sqlite3
from unittest.mock import MagicMock, patch
import pytest

# 1. ORCHESTRATION COMPONENT INGESTION AND TESTS
with patch("orchestrator.get_db_path", return_value=":memory:"):
    try:
        from orchestrator import execute_pipeline, fetch_active_steps
    except ImportError:
        from pipeline.orchestrator import execute_pipeline, fetch_active_steps

try:
    from pipeline.validators import DataQualityValidator
except ImportError:
    from validators import DataQualityValidator


@pytest.fixture
def memory_db_conn():
    """Provides a clean, isolated in-memory SQLite database setup matching production metadata schemas."""
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    # Replicate the required production control matrix schema exactly
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
    # Core target data tables required to pass internal schema check constraints safely
    cursor.execute("CREATE TABLE staging_users (id INTEGER, username TEXT);")
    cursor.execute("CREATE TABLE analytics_kpis (id INTEGER);")
    cursor.execute("CREATE TABLE summary_metrics (id INTEGER);")

    conn.commit()
    yield conn
    conn.close()


def test_fetch_active_steps_with_data(memory_db_conn):
    """Validates that active steps are retrieved correctly and sorted by execution order."""
    cursor = memory_db_conn.cursor()
    cursor.executemany(
        "INSERT INTO pipeline_metadata (step_name, target_table, execution_order, is_active) VALUES (?, ?, ?, ?);",
        [
            ("Extract Users", "staging_users", 20, 1),
            ("Disabled Ingestion", "temp_table", 5, 0),
            ("Process Analytics", "analytics_kpis", 10, 1),
        ],
    )
    memory_db_conn.commit()

    with patch("orchestrator.get_db_path", return_value=":memory:"), patch(
        "sqlite3.connect", return_value=memory_db_conn
    ):

        active_steps = fetch_active_steps()

        assert len(active_steps) == 2
        assert active_steps[0][1] == "Process Analytics"
        assert active_steps[1][1] == "Extract Users"


def test_execute_pipeline_empty_metadata(memory_db_conn):
    """Ensures the orchestration engine exits gracefully if no active rows exist."""
    # Delete metadata entries to evaluate the empty gateway warning loop accurately
    cursor = memory_db_conn.cursor()
    cursor.execute("DELETE FROM pipeline_metadata;")
    memory_db_conn.commit()

    with patch("orchestrator.get_db_path", return_value=":memory:"), patch(
        "sqlite3.connect", return_value=memory_db_conn
    ), patch("orchestrator.logger.warning") as mock_warn:

        execute_pipeline()
        mock_warn.assert_called_with(
            "No active steps found in control tables. Exiting engine flow safely."
        )


def test_execute_pipeline_successful_run(memory_db_conn):
    """Verifies complete orchestration path execution logs footprint successfully."""
    cursor = memory_db_conn.cursor()
    cursor.execute(
        "INSERT INTO pipeline_metadata (step_name, target_table, execution_order, is_active) VALUES (?, ?, ?, ?);",
        ("Extract Users", "staging_users", 10, 1),
    )
    memory_db_conn.commit()

    mock_runner = MagicMock()
    mock_runner.status = "SUCCESS"

    with patch("orchestrator.get_db_path", return_value=":memory:"), patch(
        "sqlite3.connect", return_value=memory_db_conn
    ), patch("orchestrator.DAGRunner", return_value=mock_runner), patch(
        "orchestrator.logger.info"
    ) as mock_info:

        execute_pipeline()
        mock_info.assert_any_call(
            "Metadata-driven orchestrator engine executed all tasks successfully! 🚀"
        )


# 2. VALIDATION LAYER COMPONENT TESTING FOR DATAQUALITYVALIDATOR
def test_atomic_schema_passes_valid(memory_db_conn):
    """Verifies that the database structural integrity checker handles verified configurations cleanly."""
    validator = DataQualityValidator()
    with patch("sqlite3.connect", return_value=memory_db_conn):
        result = validator.validate_atomic_schema("dummy_validation_path")
        assert result is True


def test_validate_row_record_logic():
    """Confirms individual data row attribute evaluation maps valid states accurately."""
    validator = DataQualityValidator()
    # Verifies simple data structural formats return expected boolean indicators securely
    assert (
        validator.validate_row_record(
            "staging_users", {"username": "valid_user"}
        )
        is True
    )
