-- ====================================================================
-- 1. SOURCE-TO-TARGET MAPPING LOGIC TABLE
-- ====================================================================
CREATE TABLE IF NOT EXISTS pipeline_metadata (
    pipeline_id INTEGER PRIMARY KEY AUTOINCREMENT, -- Replaces INT IDENTITY(1,1)
    pipeline_name TEXT NOT NULL UNIQUE,
    source_system TEXT NOT NULL,
    source_query_or_table TEXT NOT NULL,
    target_table TEXT NOT NULL,
    load_type TEXT DEFAULT 'INCREMENTAL',
    watermark_column TEXT,
    is_active INTEGER DEFAULT 1,                  -- SQLite uses 0 or 1 for Booleans
    created_at TEXT DEFAULT CURRENT_TIMESTAMP      -- Replaces DATETIME DEFAULT GETDATE()
);

-- ====================================================================
-- 2. PIPELINE RUN TIME PARAMETERS TABLE
-- ====================================================================
CREATE TABLE IF NOT EXISTS pipeline_parameters (
    parameter_id INTEGER PRIMARY KEY AUTOINCREMENT, -- Replaces INT IDENTITY(1,1)
    pipeline_name TEXT NOT NULL,
    parameter_key TEXT NOT NULL,
    parameter_value TEXT NOT NULL,
    description TEXT,
    FOREIGN KEY (pipeline_name) REFERENCES pipeline_metadata(pipeline_name) ON DELETE CASCADE,
    CONSTRAINT UQ_Pipeline_Key UNIQUE (pipeline_name, parameter_key)
);

-- ====================================================================
-- 3. EXECUTION LOGGING ENGINE TABLE
-- ====================================================================
CREATE TABLE IF NOT EXISTS pipeline_execution_logs (
    execution_id TEXT PRIMARY KEY,                 -- SQLite handles UUID strings seamlessly
    pipeline_name TEXT NOT NULL,
    status TEXT NOT NULL,                          -- 'RUNNING', 'SUCCESS', 'FAILED'
    start_time TEXT DEFAULT CURRENT_TIMESTAMP,     -- Replaces DATETIME DEFAULT GETDATE()
    end_time TEXT,
    rows_read INTEGER DEFAULT 0,
    rows_written INTEGER DEFAULT 0,
    error_message TEXT,
    watermark_value_loaded TEXT,
    FOREIGN KEY (pipeline_name) REFERENCES pipeline_metadata(pipeline_name)
);

-- ====================================================================
-- Seeding Baseline Configuration Records
-- ====================================================================
INSERT OR IGNORE INTO pipeline_metadata (pipeline_name, source_system, source_query_or_table, target_table, load_type, watermark_column)
VALUES ('sync_student_grades', 'Local_CSV', 'SELECT student_id, score, last_modified FROM stage_grades WHERE last_modified > ?', 'fact_student_grades', 'INCREMENTAL', 'last_modified');

INSERT OR IGNORE INTO pipeline_parameters (pipeline_name, parameter_key, parameter_value, description)
VALUES ('sync_student_grades', 'batch_size', '5000', 'Maximum rows to read per chunk execution');
