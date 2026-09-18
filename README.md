# Metadata-Driven Azure Data Factory Pipeline Framework

A high-performance, self-contained Python orchestration engine built to manage dynamic, metadata-driven data injection pipelines completely offline. 

This repository leverages an automated validation ecosystem, isolated state schemas, and built-in execution ledgers to guarantee absolute data reliability before code deployments.

---

## 🏗️ Architectural Core

The pipeline framework shifts operational parameters away from static script files and shifts them directly into a dynamic relational data structure. 

### 🗄️ Control Ledger Models
* **`pipeline_metadata`**: Stores the absolute boundaries for master workflows, handling data capture structures, target tables, and operational strategies (`INCREMENTAL` or `FULL`).
* **`pipeline_parameters`**: Manages granular operational thresholds like chunk limitations, thread sizes, and API tokens safely.
* **`pipeline_execution_logs`**: Tracks operational status metrics (`RUNNING`, `SUCCESS`, `FAILED`), data ingestion quantities, execution windows, and debugging traces automatically.

---

## 🛠️ Getting Started & Local Onboarding

### 📋 System Prerequisites
* Python 3.10 or higher
* SQLite3 database engine (Built-in standard library layer)

### ⚙️ Quick Installation Setup
1. Clone the orchestration workspace directly to your local development station:
   ```bash
   git clone https://github.com
   cd Metadata-Driven-Frame-work-pipeline
   ```

2. Establish an isolated virtual framework environment and activate it:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
   ```

3. Deploy dependencies directly from the system lock profile:
   ```bash
   pip install -r requirements-lock.txt
   ```

---

## 🧪 Verification Engine & CI/CD Pipeline

This workspace executes full quality validations automatically on every code change to guarantee production readiness.

### 🏃 Running Quality Verifications Locally
Execute the testing matrix and capture comprehensive code coverage indicators cleanly out of the terminal:
```bash
pytest --cov=adf-src/ --cov-report=term-missing
```

### 🤖 CI/CD Automation Matrix
Our GitHub Actions pipeline continuously verifies codebase health via isolated workflows:
* **Formatting Controls**: Handled on the fly by `black` styles.
* **Syntax Standardization Validation**: Checked uniformly by `flake8`.
* **Static Coding Type Validations**: Analyzed explicitly via `mypy`.
* **Automated Unit Tests Execution**: Executed independently over temporary, zero-cost memory models inside the container runner.
