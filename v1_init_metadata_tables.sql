-- ============================================================================
-- 1. SOURCE-TO-TARGET MAPPING LOGIC TABLE
-- ============================================================================
CREATE TABLE pipeline_metadata (
    pipeline_id INT IDENTITY(1,1) PRIMARY KEY,
    pipeline_name VARCHAR(100) NOT NULL UNIQUE,
    source_system VARCHAR(50) NOT NULL,       -- e.g., 'Local_CSV', 'MySQL_Mock'
    source_query_or_table VARCHAR(MAX) NOT NULL, -- Holds the exact extraction logic
    target_table VARCHAR(100) NOT NULL,       -- Destination table name
    load_type VARCHAR(20) DEFAULT 'INCREMENTAL', -- 'FULL_LOAD' or 'INCREMENTAL'
    watermark_column VARCHAR(50),             -- Column used for tracking changes (e.g., 'updated_at')
    is_active BIT DEFAULT 1,                  -- 1 = Active, 0 = Paused
    created_at DATETIME DEFAULT GETDATE()
);

-- ============================================================================
-- 2. PIPELINE RUN-TIME PARAMETERS TABLE
-- ============================================================================
CREATE TABLE pipeline_parameters (
    parameter_id INT IDENTITY(1,1) PRIMARY KEY,
    pipeline_name VARCHAR(100) NOT NULL,
    parameter_key VARCHAR(50) NOT NULL,
    parameter_value VARCHAR(255) NOT NULL,
    description VARCHAR(255),
    FOREIGN KEY (pipeline_name) REFERENCES pipeline_metadata(pipeline_name) ON DELETE CASCADE,
    CONSTRAINT UQ_Pipeline_Key UNIQUE (pipeline_name, parameter_key)
);

-- ============================================================================
-- 3. EXECUTION LOGGING ENGINE TABLE
-- ============================================================================
CREATE TABLE pipeline_execution_logs (
    execution_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    pipeline_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,              -- 'RUNNING', 'SUCCESS', 'FAILED'
    start_time DATETIME DEFAULT GETDATE(),
    end_time DATETIME,
    rows_read INT DEFAULT 0,
    rows_written INT DEFAULT 0,
    error_message VARCHAR(MAX) NULL,           -- Stores stack traces on failure
    watermark_value_loaded VARCHAR(100) NULL, -- High watermark loaded during this run
    FOREIGN KEY (pipeline_name) REFERENCES pipeline_metadata(pipeline_name)
);
-- Seed an example local tracking pipeline config
INSERT INTO pipeline_metadata (pipeline_name, source_system, source_query_or_table, target_table, load_type, watermark_column)
VALUES ('sync_student_grades', 'Local_CSV', 'SELECT student_id, score, last_modified FROM stage_grades WHERE last_modified > ?', 'dw_fact_grades', 'INCREMENTAL', 'last_modified');

-- Seed a connection timeout parameter configuration
INSERT INTO pipeline_parameters (pipeline_name, parameter_key, parameter_value, description)
VALUES ('sync_student_grades', 'batch_size', '5000', 'Maximum rows to read per chunk execution');
