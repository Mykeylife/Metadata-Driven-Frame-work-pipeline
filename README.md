# Metadata-Driven Framework Pipeline

A highly scalable, production-grade local pipeline orchestration engine built entirely in **Python** with an offline **SQLite** metadata control store and execution database tracking architecture.

---

## 1. Project Overview

This framework is a **completely local and offline** metadata-driven pipeline orchestrator designed to decouple core pipeline control flows from individual execution steps. Instead of hardcoding task lifecycles, execution properties, routing, and data paths are driven entirely by localized database parameters.

### Key Engineering Features
* **Zero Cloud Dependencies:** Operates 100% locally and offline—built specifically to optimize computational workflows without relying on pay-as-you-go cloud architectures.
* **Decoupled Architecture:** Orchestrates data task flows dynamically through parameterized database records.
* **Robust Automated Error Handling:** Features a multi-stage task runner equipped with localized execution failure recovery and automated retries.
* **Comprehensive Audit Trail:** Implements structured logging that writes atomic footprints into a centralized local execution warehouse.

---

## 2. Core Architecture & Database Schema

The orchestration engine manages pipeline life cycles by querying and updating two critical, tightly coupled tables inside a local `pipeline_metadata.db` database file:

### A. `pipeline_metadata` (The Control Table)
Tracks the overarching state and execution boundaries of registered pipeline blocks.
* `run_id` (TEXT, PK): Unique identification string for an explicit execution run.
* `pipeline_name` (TEXT): Name descriptor of the target workflow block.
* `status` (TEXT): Runtime states (`PENDING`, `RUNNING`, `SUCCESS`, `FAILED`).
* `started_at` (TEXT): ISO-8601 UTC initialization timestamp footprint.
* `ended_at` (TEXT): ISO-8601 UTC completion timestamp footprint.

### B. `execution_logs` (The Logging Table)
Captures granular, multi-stage debugging and runtime execution history linked directly to the parent runner.
* `log_id` (INTEGER, PK): Auto-incrementing identifier tracking individual task milestones.
* `run_id` (TEXT, FK): Maps logs directly back to their associated metadata control table.
* `step_name` (TEXT): Concrete operational phase being performed (e.g., `VALIDATION`, `INITIALIZATION`).
* `log_level` (TEXT): Severity layers (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`).
* `message` (TEXT): Detailed descriptive summary of the localized runtime footprint.
* `timestamp` (TEXT): Explicit timestamp recorded upon data entry.

---

## 3. Local Workspace Setup Guide

### System Requirements
* **Python 3.11+**
* **Poetry** (or a local dependency builder mapping via standard packaging utilities)

### Installation
1. Clone this repository directly into your local machine environment:
   ```bash
   git clone https://github.com/Mykeylife/Metadata-Driven-Frame-work-pipeline.git
   cd Metadata-Driven-Frame-work-pipeline
   ```

2. Establish dependencies and lock environments using Poetry:
   ```bash
   poetry install
   ```
   *(Alternatively, run `pip install -r requirements.txt` to align tools within raw python runtime containers).*

---

## 4. Test Suite Execution & Code Quality Gates

This repository enforces strict code quality and linting baselines verified continuously through a localized automated CI framework.

### Running Local Unit Tests
Validate execution mocks, logic paths, and database schema connections by invoking:
```bash
poetry run coverage run -m unittest discover
```

### Viewing Code Quality Coverage Reports
Ensure that total project test coverage stays strictly above the required **80% quality gate** baseline:
```bash
poetry run coverage report
```

### Formatting and Syntax Compliance
Check line constraints and coding syntax styles prior to creating repository commits:
```bash
poetry run black .
poetry run flake8 .
```

---

## 5. Deployment Options (Docker Containerization)

For self-contained container deployments, compile and run the engine using the localized production configuration layout:
```bash
docker build -t metadata-orchestrator .
docker run --rm metadata-orchestrator
```
