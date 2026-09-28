import os
from pathlib import Path
from typing import Optional

# FIX: Leverage Pathlib to calculate the absolute database file location path dynamically
BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = str(BASE_DIR / "metadata_control.db")


def get_db_path() -> str:
    """Returns the centralized absolute database path, allowing an environment override for flexibility."""
    return os.getenv("PIPELINE_DB_PATH", DEFAULT_DB_PATH)


def get_webhook_url() -> Optional[str]:
    """Retrieves the messaging platform webhook URL from the environment vector configuration."""
    return os.getenv("PIPELINE_WEBHOOK_URL")
    
