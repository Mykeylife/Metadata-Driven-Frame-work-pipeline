"""Centralized configuration manager for the metadata-driven framework.

Handles environment vector tracking, absolute database mapping paths,
and messaging platform alerting telemetry endpoints.
"""

import os
from pathlib import Path
from typing import Optional

# Compute absolute pathing constraints relative to the module root layout
BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = str(BASE_DIR / "metadata_control.db")


def get_db_path() -> str:
    """Retrieves the operational SQLite tracking store path constraint.
    
    Checks environment configurations and dynamically falls back to the 
    canonical absolute project root file path location.
    
    Returns:
        str: Absolute or configured path to the SQLite metadata database.
    """
    db_path = os.getenv("PIPELINE_DB_PATH")
    if not db_path:
        return DEFAULT_DB_PATH
    return str(Path(db_path).resolve())


def get_webhook_url() -> Optional[str]:
    """Extracts the telemetry communication channel webhook endpoint.
    
    Returns:
        Optional[str]: Webhook destination URL string if set, otherwise None.
    """
    webhook_url = os.getenv("PIPELINE_WEBHOOK_URL")
    if not webhook_url or not webhook_url.strip():
        return None
    return webhook_url.strip()
