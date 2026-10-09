-- ====================================================================
-- 1. CORE PIPELINE CONTROL & SEQUENCE MAPPING TABLE
-- ====================================================================
CREATE TABLE IF NOT EXISTS pipeline_metadata (
    step_id INTEGER PRIMARY KEY AUTOINCREMENT,
    step_name TEXT NOT NULL UNIQUE,
    target_table TEXT NOT NULL,
    execution_order INTEGER NOT NULL,
    is_active INTEGER DEFAULT 1
);

-- ====================================================================
-- 2. GRANULAR AUDIT LOGGING & TELEMETRY ENGINE TABLE
-- ====================================================================
CREATE TABLE IF NOT EXISTS pipeline_execution_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    step_name TEXT NOT NULL,
    status TEXT NOT NULL,                          -- 'RUNNING', 'SUCCESS', 'FAILED', 'CRITICAL'
    execution_time TEXT NOT NULL,                  -- Microsecond runtime tracking
    error_message TEXT
);

-- ====================================================================
-- 3. BUSINESS INGESTION & DATA TRANSFORMATION LAYERS
-- ====================================================================
CREATE TABLE IF NOT EXISTS staging_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS analytics_kpis (
    kpi_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    username_length INTEGER NOT NULL,
    processed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS summary_metrics (
    summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT NOT NULL,
    metric_value TEXT NOT NULL,
    calculated_at TEXT NOT NULL
);

-- ====================================================================
-- Seeding Baseline Operational Metadata Records
-- ====================================================================
INSERT OR IGNORE INTO pipeline_metadata (step_name, target_table, execution_order, is_active)
VALUES 
('staging_users', 'staging_users', 1, 1),
('analytics_kpis', 'analytics_kpis', 2, 1),
('summary_metrics', 'summary_metrics', 3, 1);
