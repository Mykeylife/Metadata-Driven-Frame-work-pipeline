# 🗺️ Centralized Orchestration Feature Roadmap & Task Matrix

This document tracks the explicit design parameters, implementation states, and technical dependencies for upcoming data engineering orchestration features.

---

## 📊 Core Feature Matrix

| Feature Module | Primary Focus | Dependencies | Status | Target Layer |
| :--- | :--- | :--- | :--- | :--- |
| **Advanced Biometrics Logging** | CPU & Memory footprint profiling | `pipeline/dag_runner.py` | ⏳ Planned | Telemetry Logs |
| **Savepoint Transactions** | Multi-stage task rollbacks | `sqlite3.Connection` | ⏳ Planned | Storage Layer |
| **Adaptive Retry Backoff** | Exponential backoff loops | `time.sleep` | 📅 Backlog | Engine Runtime |
| **JSON Parameter Parsing** | Dynamic out-of-band input schemas | `pipeline/config.py` | 📅 Backlog | Configuration |

---

## 🛠️ Step-by-Step Task Blueprints

### 1. Advanced System Biometrics Logging
Capture actual system computing constraints instead of static runtime durations.
- [ ] **Table Update**: Append `cpu_utilization_ratio` (REAL) and `peak_memory_bytes` (INTEGER) fields into the `pipeline_execution_logs` schema definition.
- [ ] **Profiler Utility**: Integrate Python's native `psutil` or `resource` library measurements into the tracking loop.
- [ ] **State Capturing**: Update `DAGRunner.log_execution` to collect process biometric snapshots exactly when a task concludes.

### 2. Savepoint Database Transaction Containment
Isolate execution failures cleanly so faulty tasks do not leave partial, corrupted records inside database targets.
- [ ] **Context Safe Guards**: Wrap block transformations inside explicit `SAVEPOINT step_name;` and `RELEASE SAVEPOINT step_name;` queries.
- [ ] **Rollback Routines**: If a database error or constraint violation drops mid-step, execute `ROLLBACK TO SAVEPOINT step_name;` before firing your out-of-band WebHook alerts.
- [ ] **Test Coverage**: Build a unit test suite to intentionally inject bad data and verify the database rolls back atomically while the framework audit logs track the failure seamlessly.

---

## 🛡️ Core Verification Quality Gates
* **CI Integration**: New feature branches are strictly barred from merging unless all automated **pytest** workflow assertions remain 100% green.
* **Coverage Margin**: Maintain overall project code coverage above your required **85% quality gate threshold**.
