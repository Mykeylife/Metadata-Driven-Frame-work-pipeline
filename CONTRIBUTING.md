# Contributing to Metadata-Driven-Frame-work-pipeline

Thank you for taking the time to contribute to the Metadata-Driven Pipeline Framework! This document outlines the engineering guidelines, repository workflows, and code quality expectations for developers looking to expand this orchestration engine.

---

## 1. Code of Conduct

We are committed to fostering an open, professional, and welcoming developer environment. We expect all contributors to maintain respectful communication, deliver high-quality documentation, and follow standard open-source collaboration practices.

---

## 2. Setting Up Your Development Environment

This framework uses **Python 3.11+**, **SQLite**, and **Poetry** for package dependency and virtual environment management. Follow these steps to spin up your local instance:

1. **Clone the Repository:**
   ```bash
   git clone https://github.com
   cd Metadata-Driven-Frame-work-pipeline
   ```

2. **Install Dependencies via Poetry:**
   ```bash
   poetry install
   ```

3. **Initialize the Metadata Database Schema:**
   ```bash
   poetry run python -c "import sqlite3; conn = sqlite3.connect('pipeline_metadata.db');"
   ```

4. **Verify the Installation by Running Tests:**
   ```bash
   poetry run coverage run -m unittest discover
   ```

---

## 3. Engineering Workflows & Branching Policy

To maintain a clean engineering history capable of sustaining granular tasks, please adhere to our strict branch architecture:

* **Main Branch (`main`):** Production-ready, locked branch. Code must pass all quality gates before landing here.
* **Feature Branches (`feat/`):** Used for introducing new pipeline features, connectors, or orchestration mechanics (e.g., `feat/retry-logic`).
* **Fix Branches (`fix/`):** Used for fixing syntax bugs, database locking issues, or failing mock assertions (e.g., `fix/test-assertions`).

### Submitting a Pull Request (PR)
1. Branch off of `main` using a descriptive task label.
2. Complete your code changes across targeted, atomic commits.
3. Ensure your module additions have corresponding test suites inside `test_orchestrator.py`.
4. Open a Pull Request targeting `main`, outlining the specific problem solved and passing test outputs.

---

## 4. Strict Quality Gates & Coding Standards

All code submissions are automatically vetted by our GitHub Actions CI pipeline against our configuration rules:

### Code Style & Formatting
* **Formatter (`black`):** Code must be strictly formatted according to Black's standard 88-character line limit rules. Run `poetry run black .` before pushing.
* **Linter (`flake8`):** Code must produce zero warnings or errors when processed through our custom `.flake8` configurations.

### Test Coverage Minimums
* **Coverage Floor:** The project maintains a strict test validation block set to **80% coverage**.
* If a new feature drops total application coverage below the 80% mark, the quality gate runner will fail the build, and the PR will be blocked from merging.

---

## 5. Reporting Bugs & Suggesting Enhancements

If you encounter execution errors or database locking alerts:
1. Navigate to the **Issues** tab on GitHub.
2. Open a new issue with a clear summary title.
3. Provide your environment details (OS, Python version), the exact logs from your execution tracking tables, and a minimal reproducible code snippet.
