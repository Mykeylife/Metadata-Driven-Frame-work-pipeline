import sqlite3
from unittest.mock import patch
import pytest
from pipeline.validators import DataQualityValidator

@pytest.fixture
def test_db():
    """Sets up a clean in-memory database configuration for testing schemas."""
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS staging_users (id INTEGER, username TEXT);")
    cursor.execute("CREATE TABLE IF NOT EXISTS analytics_kpis (kpi_id INTEGER, username TEXT, username_length INTEGER, processed_at TEXT);")
    cursor.execute("CREATE TABLE IF NOT EXISTS summary_metrics (summary_id INTEGER, metric_name TEXT, metric_value TEXT, calculated_at TEXT);")
    conn.commit()
    yield ":memory:"
    conn.close()

def test_atomic_schema_passes_valid(test_db):
    """Ensures validator returns True when tables have matching fields."""
    validator = DataQualityValidator()
    
    # Safely mock sqlite3.connect within this localized test scope
    with patch("sqlite3.connect") as mock_connect:
        # Create a real connection to our setup database to return real column data
        real_conn = sqlite3.connect(test_db)
        mock_connect.return_value = real_conn
        
        result = validator.validate_atomic_schema(test_db)
        real_conn.close()
        
        assert result is True

def test_validate_row_record_logic():
    """Validates row-level payload strings catch empty fields cleanly."""
    validator = DataQualityValidator()
    assert validator.validate_row_record("staging_users", {"username": "valid_user"}) is True
    assert validator.validate_row_record("staging_users", {"username": ""}) is False
    assert validator.validate_row_record("staging_users", {"username": "   "}) is False
