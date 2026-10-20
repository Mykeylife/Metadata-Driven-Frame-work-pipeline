"""Unit tests verifying custom tracking model annotations."""

from datetime import datetime

from pipeline.models import PipelineExecutionError, PipelineRun


def test_pipeline_run_dataclass_properties():
    """Validates parameter setting capabilities inside data models."""
    now = datetime.now()
    run = PipelineRun(run_id="RUN_123", pipeline_name="Ingestion", status="SUCCESS", started_at=now)
    assert run.run_id == "RUN_123"
    assert run.ended_at is None


def test_pipeline_error_exception_raising():
    """Ensures standard orchestrator custom error triggers follow expected patterns."""
    try:
        raise PipelineExecutionError("Structural Failure Execution.")
    except PipelineExecutionError as error:
        assert str(error) == "Structural Failure Execution."
