CREATE TABLE IF NOT EXISTS pipeline_execution_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    step_name TEXT NOT NULL,
    status TEXT NOT NULL,
    execution_time TEXT NOT NULL,
    error_message TEXT
);
