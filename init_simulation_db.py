# init_simulation_db.py
import sqlite3

def init_db(db_path: str = "simulation.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Use CREATE TABLE IF NOT EXISTS to prevent destroying existing history
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS execution_logs (
            run_id TEXT PRIMARY KEY,
            pipeline_name TEXT NOT NULL,
            status TEXT NOT NULL,
            started_at TEXT NOT NULL,
            ended_at TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_metadata (
            pipeline_name TEXT PRIMARY KEY,
            is_active INTEGER DEFAULT 1
        )
    """)
    
    # Safe seed logic using INSERT OR IGNORE
    cursor.execute("""
        INSERT OR IGNORE INTO pipeline_metadata (pipeline_name, is_active)
        VALUES ('Metadata-Driven-Frame-work-pipeline', 1)
    """)
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
