import unittest
import sqlite3
from unittest.mock import patch

# 1. MAKE SURE TO IMPORT YOUR ACTUAL ORCHESTRATOR CODE
# Assuming your file is named orchestrator.py in the root or a folder:
import orchestrator 

class TestMetadataPipelineOrchestrator(unittest.TestCase):

    def setUp(self):
        """Set up an in-memory SQLite database mimicking the real pipeline_metadata schema."""
        self.connection = sqlite3.connect(":memory:")
        self.cursor = self.connection.cursor()
        
        # Create the pipeline_metadata tracking table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_metadata (
                run_id TEXT PRIMARY KEY,
                pipeline_name TEXT,
                status TEXT,
                started_at TEXT,
                ended_at TEXT
            )
        """)
        
        # Create the execution log tracking table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS execution_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT,
                step_name TEXT,
                log_level TEXT,
                message TEXT,
                timestamp TEXT,
                FOREIGN KEY(run_id) REFERENCES pipeline_metadata(run_id)
            )
        """)
        self.connection.commit()

    def tearDown(self):
        """Clean up the test environment database."""
        self.connection.close()

    @patch('sqlite3.connect')
    def test_orchestrator_execution_flow(self, mock_connect):
        """Test that the orchestrator reads metadata and writes logs correctly."""
        # Force the connection to use our in-memory database
        mock_connect.return_value = self.connection
        
        # Insert a test row
        self.cursor.execute(
            "INSERT INTO pipeline_metadata (run_id, pipeline_name, status) VALUES (?, ?, ?)",
            ("run_test_001", "Metadata-Driven-Pipeline", "PENDING")
        )
        self.connection.commit()

        # 2. ACTIVELY RUN YOUR ORCHESTRATOR CODE (Uncommented)
        # Adjust this function name to match whatever execution function is inside your orchestrator.py
        status = orchestrator.run_pipeline("run_test_001", db_conn=self.connection)
        self.assertEqual(status, "SUCCESS")

        # 3. ACTIVELY VERIFY LOG VALUES (Uncommented)
        self.cursor.execute("SELECT step_name, log_level FROM execution_logs WHERE run_id = ?", ("run_test_001",))
        logs_written = self.cursor.fetchall()
        
        # Assert that your logic populated rows to your logging metrics
        self.assertTrue(len(logs_written) > 0)

if __name__ == '__main__':
    unittest.main()
