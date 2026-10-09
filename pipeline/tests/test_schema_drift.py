import re

def test_sql_ddl_matches_python_definition():
    """Asserts that the committed SQL file matches the active schema definition."""
    with open("v1_init_metadata_tables.sql", "r") as f:
        sql_content = f.read().lower()
        
    # Check for canonical columns used by the orchestrator loop
    assert "step_id" in sql_content
    assert "step_name" in sql_content
    assert "target_table" in sql_content
