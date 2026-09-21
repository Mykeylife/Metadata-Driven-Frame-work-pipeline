import sqlite3

def setup_simulation():
    # Connects to the local simulation SQLite database file
    conn = sqlite3.connect('metadata_store.db')
    cursor = conn.cursor()
    
    print("Initializing simulation database architecture tables...")
    
    # 1. Drop old mismatched tables if they exist to start fresh
    cursor.execute("DROP TABLE IF EXISTS pipeline_logs")
    cursor.execute("DROP TABLE IF EXISTS execution_logs")
    cursor.execute("DROP TABLE IF EXISTS pipeline_metadata")
    
    # 2. Create the master control table (pipeline_metadata)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pipeline_metadata (
            run_id TEXT PRIMARY KEY,
            pipeline_name TEXT NOT NULL,
            status TEXT CHECK(status IN ('PENDING', 'RUNNING', 'SUCCESS', 'FAILED')) DEFAULT 'PENDING',
            started_at TEXT,
            ended_at TEXT
        )
    ''')
    
    # 3. Create the granular logging table (execution_logs)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS execution_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            step_name TEXT CHECK(step_name IN ('VALIDATION', 'INITIALIZATION', 'EXECUTION', 'CLEANUP')) NOT NULL,
            log_level TEXT CHECK(log_level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')) DEFAULT 'INFO',
            message TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(run_id) REFERENCES pipeline_metadata(run_id)
        )
    ''')
    
    # 4. Inject mock control data matching your execution states
    mock_pipelines = [
        ('RUN_20260921_01', 'Customer_Data_Ingestion', 'SUCCESS', '2026-09-21T20:00:00Z', '2026-09-21T20:02:15Z'),
        ('RUN_20260921_02', 'Sales_Metrics_Aggregation', 'FAILED', '2026-09-21T21:15:00Z', '2026-09-21T21:16:40Z'),
        ('RUN_20260921_03', 'Inventory_Cleanup_Job', 'RUNNING', '2026-09-21T22:00:00Z', None)
    ]
    
    cursor.executemany('''
        INSERT INTO pipeline_metadata (run_id, pipeline_name, status, started_at, ended_at)
        VALUES (?, ?, ?, ?, ?)
    ''', mock_pipelines)
    
    # 5. Inject matching telemetry logs for the failed pipeline to provide debugging contexts
    mock_logs = [
        ('RUN_20260921_02', 'INITIALIZATION', 'INFO', 'Starting simulation run components.'),
        ('RUN_20260921_02', 'VALIDATION', 'INFO', 'Schema parsing constraint checks completed successfully.'),
        ('RUN_20260921_02', 'EXECUTION', 'ERROR', 'Database execution timeout: target connection refused.')
    ]
    
    cursor.executemany('''
        INSERT INTO execution_logs (run_id, step_name, log_level, message)
        VALUES (?, ?, ?, ?)
    ''', mock_logs)
    
    conn.commit()
    print("Simulation setup complete! Metadata control and execution logs match requirements.")
    conn.close()

if __name__ == "__main__":
    setup_simulation()
