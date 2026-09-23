# models.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class PipelineRun:
    run_id: str
    pipeline_name: str
    status: str
    started_at: datetime
    ended_at: Optional[datetime] = None

class PipelineExecutionError(Exception):
    """Raised when an error occurs during pipeline orchestration or task management."""
    pass
