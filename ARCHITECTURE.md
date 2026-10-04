# System Architecture: Metadata-Driven Pipeline Orchestrator

This document outlines the architectural design, data flow, and database schema for the **Metadata-Driven Framework Pipeline**.

## 1. Core Design Principles

The orchestrator is built on a **metadata-driven** paradigm. Instead of hardcoding execution paths, task orders, or target tables in Python scripts, the pipeline behavior is dynamically defined inside an underlying relational database engine.

* **Decoupling:** Execution logic is cleanly isolated from operational configurations.
* **Idempotency:** Pipelines can run repeatedly without corrupting data or creating duplicates.
* **Fault Isolation:** Structural failures in a given task block dependent nodes without corrupting adjacent DAG lineages.

---

## 2. High-Level Component Layout

