# Metadata-Driven Framework Pipeline

A scalable local pipeline orchestration engine built in Python featuring an offline SQLite metadata control store, metrics generation, and live execution telemetry.

For complete documentation, database schemas, and installation steps, please visit the [GitHub Repository](https://github.com/Mykeylife/Metadata-Driven-Frame-work-pipeline.git).

## Overview & Architecture
The framework decouples pipeline control flows from execution steps using localized database configurations instead of hardcoded task lifecycles. It operates completely offline with zero cloud dependencies, implements pre- and post-processing quality gate assertions, and features webhook telemetry for real-time alerting.

The database architecture utilizes control tables (`pipeline_metadata`, `pipeline_execution_logs`) alongside business data layers (`staging_users`, `analytics_kpis`, `summary_metrics`).

## Quick Setup & Usage
1. **Requirements:** Python 3.11+ and Poetry.
2. **Environment Configuration:**
   ```bash
   export PIPELINE_DB_PATH="metadata_control.db"
   export PIPELINE_WEBHOOK_URL="https://discord.com"
   ```
3. **Installation:**
   ```bash
   git clone https://github.com/Mykeylife/Metadata-Driven-Frame-work-pipeline.git
   cd Metadata-Driven-Frame-work-pipeline
   poetry install
   ```
4. **Database Initialization:**
   ```bash
   poetry run init-db
   ```
5. **Execution & Testing:** Run unit tests via `poetry run pytest -v` or build via Docker containers.
