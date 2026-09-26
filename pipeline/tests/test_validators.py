import sqlite3
import pytest
from pipeline.validators import DataQualityValidator


@pytest.fixture
def test_db():
    """Builds an ephemeral database connection populated with structural testing data configurations."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("CREATE TABLE staging_users (id INTEGER PRIMARY KEY, username TEXT);")
    cursor.execute("INSERT INTO staging_users (username) VALUES ('Olanrewaju'), ('Myke_Dev');")
    
    conn.commit()
    yield conn
    conn.close()


def test_validator_row_count_and_null_gates(test_db, monkeypatch):
    """Verifies row count and null checking logic functions pass accurately on safe schemas."""
    validator = DataQualityValidator(db_path=":memory:")
    monkeypatch.setattr(validator, "_get_db_connection", lambda: test_db)
    
    assert validator.check_row_count("staging_users", min_expected=1) is True
    assert validator.check_null_threshold("staging_users", column_name="id", max_allowed_pct=0.0) is True


def test_validator_catches_syntax_breaches(test_db, monkeypatch):
    """Ensures syntax pattern checking flags non-compliant record insertions perfectly."""
    validator = DataQualityValidator(db_path=":memory:")
    monkeypatch.setattr(validator, "_get_db_connection", lambda: test_db)
    
    # Assert healthy data passes cleanly
    assert validator.check_syntax_constraints("staging_users", column_name="username") is True
    
    # Inject a non-compliant profile format string row to trigger validation drops
    cursor = test_db.cursor()
    cursor.execute("INSERT INTO staging_users (username) VALUES ('invalid@user!');")
    test_db.commit()
    
    assert validator.check_syntax_constraints("staging_users", column_name="username") is False


def test_validate_step_orchestration_loop(test_db, monkeypatch):
    """Confirms step orchestration gates evaluate compound parameters seamlessly."""
    validator = DataQualityValidator(db_path=":memory:")
    monkeypatch.setattr(validator, "_get_db_connection", lambda: test_db)
    
    task_param = {"target_table": "staging_users"}
    assert validator.validate_step(task_param) is True
