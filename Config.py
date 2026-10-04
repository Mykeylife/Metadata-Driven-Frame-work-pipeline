"""Pipeline configuration and database path management."""
import os
from pathlib import Path

def get_db_path() -> str:
    """
    Returns the path to the SQLite metadata database.
    Defaults to 'metadata_store.db' in the repository root.
    """
    db_path = os.getenv('PIPELINE_DB_PATH', 'metadata_store.db')
    return db_path
