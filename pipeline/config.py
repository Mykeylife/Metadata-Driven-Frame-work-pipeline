import os

# Centralized default storage path constant string
DEFAULT_DB_PATH = "metadata_control.db"


def get_db_path() -> str:
    """Returns the centralized database path, allowing an environment override for flexibility."""
    return os.getenv("PIPELINE_DB_PATH", DEFAULT_DB_PATH)


def get_webhook_url() -> Optional[str]:
    """Retrieves the messaging platform webhook URL from the environment vector configuration."""
    return os.getenv("PIPELINE_WEBHOOK_URL")
    
