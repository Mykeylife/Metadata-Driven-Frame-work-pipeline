"""Centralized parameter catalog management for the metadata control store configuration blocks."""

import os


def get_db_path() -> str:
    """Resolves and returns the fully qualified target filepath endpoint for the SQLite control store."""
    return os.getenv("DB_PATH", "metadata_control.db")
