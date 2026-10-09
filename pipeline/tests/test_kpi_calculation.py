import pytest
from pipeline.kpi_calculator import compute_user_kpis

def test_compute_user_kpis_empty_input():
    assert compute_user_kpis(None, []) == []

def test_compute_user_kpis_valid_data():
    results = compute_user_kpis(None, ["mykeylife", "testuser"])
    assert len(results) == 2
    assert results[0][0] == "mykeylife"
    assert results[0][1] == 9  # character length
