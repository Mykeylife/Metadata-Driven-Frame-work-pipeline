import sqlite3

def setup_simulation():
    # Connects to a local SQLite database file
    conn = sqlite3.connect('metadata_store.db')
    cursor = conn.cursor()
    
    print("Initializing simulation database control tables...")
    
    # 1. Create the pipeline control table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pipeline_metadata (
            pipeline_id TEXT PRIMARY KEY,
            pipeline_name TEXT NOT NULL,
            source_type TEXT NOT NULL,
            target_type TEXT NOT NULL,
            status TEXT DEFAULT 'ACTIVE',
            last_run_timestamp TEXT
        )
    ''')
    
    # 2. Create the pipeline logging audit table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pipeline_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            pipeline_id TEXT,
            status TEXT NOT NULL,
            records_processed INTEGER,
            error_message TEXT,
            execution_time REAL,
            run_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(pipeline_id) REFERENCES pipeline_metadata(pipeline_id)
        )
    ''')
    
    # 3. Inject mock control data for testing
    mock_pipelines = [
        ('PL_001', 'Customer_Sync_Pipeline', 'CSV', 'SQLite', 'ACTIVE', None),
        ('PL_002', 'Sales_Aggregation_Pipeline', 'JSON', 'Postgres_Mock', 'ACTIVE', None),
        ('PL_003', 'Inventory_Cleanup_Job', 'API_Mock', 'SQLite', 'INACTIVE', None)
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO pipeline_metadata 
        (pipeline_id, pipeline_name, source_type, target_type, status, last_run_timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', mock_pipelines)
    
    conn.commit()
    print("Simulation tables created successfully with 3 active mock pipelines!")
    
    # Verify the injection
    cursor.execute("SELECT COUNT(*) FROM pipeline_metadata")
    print(f"Total pipelines configured in simulation: {cursor.fetchone()[0]}")
    
    conn.close()

if __name__ == "__main__":
    setup_simulation()
