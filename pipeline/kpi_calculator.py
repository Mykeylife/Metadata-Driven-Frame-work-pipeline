"""Decoupled transformation rules for metrics computing layers."""

import logging
from typing import Any

from .validators import DataQualityValidator

logger = logging.getLogger("dag_runner.kpi_calculator")


def process_aggregate_metrics(cursor: Any, users: list[Any], validator: DataQualityValidator) -> None:
    """Validates records, extracts depths, and pushes analytics safely down to targets."""
    valid_users = []
    for u in users:
        row_dict = dict(u) if u else {}
        if validator.validate_row_record("staging_users", row_dict):
            valid_users.append(u)
        else:
            logger.warning("Skipping individual corrupted data record inside staging sweep.")

    if not valid_users:
        logger.warning("No valid rows passed the data quality threshold for calculations.")
        return

    max_len = max(len(u["username"]) for u in valid_users if u["username"])

    from .repository import insert_analytics_kpi, insert_summary_metric

    insert_summary_metric(cursor, "max_username_length", str(max_len))

    for user in valid_users:
        username = user["username"]
        if username:
            insert_analytics_kpi(cursor, username, len(username))
