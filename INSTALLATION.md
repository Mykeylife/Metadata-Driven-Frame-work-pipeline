# Installation and Setup Guide

Follow these guidelines to set up, configure, and execute the Metadata-Driven Pipeline Orchestrator on your environment.

## 1. Prerequisites

Before starting, ensure your system meets the following software criteria:
* **Python:** Version `3.11` or higher.
* **Package Manager:** `Poetry` installed on your machine.

If you do not have Poetry configured yet, install it via:
```bash
curl -sSL https://python-poetry.org | python3 -
```

---

## 2. Local Environment Setup

Clone your repository to your local system and navigate into the target folder project path:

```bash
# Clone the repository
git clone https://github.com

# Move into the package root
cd Metadata-Driven-Frame-work-pipeline
```

### Dependency Installation
Use Poetry to isolate your virtual environment environment packages cleanly:

```bash
poetry install
```
This command sets up production code dependencies as well as code quality frameworks like `mypy`, `black`, and `flake8`.

---

## 3. Database Ingestion Initialization

The framework requires seed metadata tables to run properly. Run the built-in database simulation initializer script using your Poetry environment shortcut runner:

```bash
poetry run python init_simulation_db.py
```
*Note: This creates your tracking tables, populates sample execution order rows, and hooks up paths cleanly.*

---

## 4. Running the Engine Flow

To run the full orchestrator ingestion cycle manually, execute:

```bash
poetry run python orchestrator.py
```

---

## 5. Verification Check Frameworks

### Code Quality Gates
Run your static type analyzers, format checks, and testing suites locally to match your GitHub Actions CI/CD metrics:

```bash
# Code layout formatting check
poetry run black --check .

# Lint validation check
poetry run flake8 .

# Static type accuracy verification
poetry run mypy .

# Operational unit tests
poetry run pytest
```
