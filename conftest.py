import os
import sqlite3

import pytest


@pytest.fixture
def clean_db_conn():
    """Dynamically seeds an in-memory SQLite database using the project DDL file."""
    # help: Organize imports

    sql_path = "v1_init_metadata_tables.sql"

    if os.path.exists(sql_path):
        with open(sql_path) as f:
            sql_script = f.read()
            # Execute the entire script block (creating all 5 tables + seeding metadata records)

    # ... keep the rest of your clean_db_conn fixture logic down here ...
