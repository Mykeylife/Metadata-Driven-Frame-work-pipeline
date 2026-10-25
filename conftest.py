import os
import sqlite3

import pytest


@pytest.fixture
def clean_db_conn():
    """Dynamically seeds an in-memory SQLite database using the project DDL file."""
    sql_path = "v1_init_metadata_tables.sql"

    # Create the in-memory SQLite connection
    conn = sqlite3.connect(":memory:")

    if os.path.exists(sql_path):
        with open(sql_path) as f:
            sql_script = f.read()
            # Execute the DDL script against the connection to create and seed tables
            conn.executescript(sql_script)

    yield conn
    conn.close()
    
