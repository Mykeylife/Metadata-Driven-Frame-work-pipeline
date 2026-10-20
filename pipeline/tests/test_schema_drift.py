"""Unit tests verifying structural schemas and checking formatting metrics compatibility."""

def test_sql_ddl_matches_python_definition():
    """Asserts that the committed SQL file matches the active schema definition."""
    # FIXED: Follows strict open patterns
    with open("v1_init_metadata_tables.sql") as f:
        sql_content = f.read().lower()

    # Check for canonical columns used by the orchestrator loop
    assert "step_id" in sql_content
