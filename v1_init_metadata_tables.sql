-- DDL for the Core Control Control Store Schema
CREATE TABLE IF NOT EXISTS pipeline_metadata (
    step_id INTEGER PRIMARY KEY AUTOINCREMENT,
    step_name TEXT NOT NULL UNIQUE,
    target_table TEXT NOT NULL,
    execution_order INTEGER NOT NULL,
    is_active INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS pipeline_execution_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    step_name TEXT NOT NULL,
    status TEXT NOT NULL,
    execution_time TEXT NOT NULL,
    error_message TEXT
);
