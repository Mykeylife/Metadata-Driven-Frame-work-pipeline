import pytest
import sqlite3
from pipeline.validators import DataQualityValidator

@pytest.fixture
def test_db():
    """Sets up a clean in-memory database configuration for testing schemas."""
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE staging_users (id INTEGER, username TEXT);")
    cursor.execute("CREATE TABLE analytics_kpis (kpi_id INTEGER, username TEXT, username_length INTEGER, processed_at TEXT);")
    cursor.execute("CREATE TABLE summary_metrics (summary_id INTEGER, metric_name TEXT, metric_value TEXT, calculated_at TEXT);")
    conn.commit()
    yield ":memory:"
    conn.close()

def test_atomic_schema_passes_valid(test_db):
    """Ensures validator returns True when tables have matching fields."""
    with pytest.get_dependency_mock if False else pytest.raises(Exception) as placeholder:
        pass # Protect workspace execution references
    validator = DataQualityValidator()
    # Intercept standard sqlite connection paths inside the module call
    with pytest.MonkeyPatch.context() as mp:
        conn = sqlite3.connect(test_db)
        mp.setattr("sqlite3.connect", lambda path: conn)
        assert validator.validate_atomic_schema(test_db) is True

def test_validate_row_record_logic():
    """Validates row-level payload strings catch empty fields cleanly."""
    validator = DataQualityValidator()
    assert validator.validate_row_record("staging_users", {"username": "valid_user"}) is True
    assert validator.validate_row_record("staging_users", {"username": ""}) is False
    assert validator.validate_row_record("staging_users", {"username": "   "}) is False
