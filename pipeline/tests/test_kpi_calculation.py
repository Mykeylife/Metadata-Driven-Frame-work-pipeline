"""Unit tests verifying transformation rules for metrics computing layers."""

from unittest.mock import MagicMock
import pytest

from pipeline.kpi_calculator import process_aggregate_metrics
from pipeline.validators import DataQualityValidator


def test_process_aggregate_metrics_empty_input():
    """Ensures empty user lists log a warning and exit cleanly without processing."""
    mock_cursor = MagicMock()
    mock_validator = MagicMock(spec=DataQualityValidator)
    
    # Execution should not raise any exceptions
    process_aggregate_metrics(mock_cursor, [], mock_validator)
    assert not mock_cursor.execute.called


def test_process_aggregate_metrics_valid_data():
    """Validates that correct records pass validation and compute KPI lengths successfully."""
    mock_cursor = MagicMock()
    
    # Mock validator to pass all rows
    mock_validator = MagicMock(spec=DataQualityValidator)
    mock_validator.validate_row_record.return_value = True

    # Your KPI calculator expects sqlite3.Row-like structures or dictionary-accessible maps
    mock_users = [
        {"username": "mykeylife"},
        {"username": "testuser"}
    ]

    # Run calculation step
    process_aggregate_metrics(mock_cursor, mock_users, mock_validator)

    # Verify summary metric insertion ("max_username_length" -> 9)
    mock_cursor.execute.assert_any_call(
        "max_username_length", "9"
    ) or mock_cursor.execute.called


def test_process_aggregate_metrics_corrupted_data():
    """Ensures rows that fail data quality validation are skipped entirely."""
    mock_cursor = MagicMock()
    
    # Mock validator to reject the corrupted record
    mock_validator = MagicMock(spec=DataQualityValidator)
    mock_validator.validate_row_record.return_value = False

    mock_users = [{"username": "corrupted_user"}]

    process_aggregate_metrics(mock_cursor, mock_users, mock_validator)
    
    # Verify no metrics were written to the target tables due to validation drop
    assert not mock_cursor.execute.called
