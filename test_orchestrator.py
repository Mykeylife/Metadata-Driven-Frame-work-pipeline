import unittest
import sqlite3
from unittest.mock import patch
# Importing the actual pipeline engine logic from your root orchestrator module
import orchestrator

class TestMetadataPipelineOrchestrator(unittest.TestCase):

    def setUp(self):
        """Set up an in-memory SQLite database mimicking the real pipeline schema."""
        self.connection = sqlite3.connect(":memory:")
        self.cursor = self.connection.cursor()

        # 1. Create the pipeline_metadata tracking table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_metadata (
                run_id TEXT PRIMARY KEY,
                pipeline_name TEXT NOT NULL,
                status TEXT CHECK(status IN ('PENDING', 'RUNNING', 'SUCCESS', 'FAILED')) DEFAULT 'PENDING',
                started_at TEXT,
                ended_at TEXT
            )
        """)

        # 2. Create the execution log tracking table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS execution_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                step_name TEXT CHECK(step_name IN ('VALIDATION', 'INITIALIZATION', 'EXECUTION', 'CLEANUP')) NOT NULL,
                log_level TEXT CHECK(log_level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')) DEFAULT 'INFO',
                message TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(run_id) REFERENCES pipeline_metadata(run_id)
            )
        """)
        self.connection.commit()

    def tearDown(self):
        """Clean up the test environment database."""
        self.connection.close()

    @patch("sqlite3.connect")
    def test_orchestrator_execution(self, mock_connect):
        """Test that the orchestrator reads metadata and writes logs correctly."""
        # Force the orchestrator connection parameters to use our active in-memory database
        mock_connect.return_value = self.connection

        # 1. Insert an initial test row with PENDING state
        self.cursor.execute("""
            INSERT INTO pipeline_metadata (run_id, pipeline_name, status)
            VALUES ('run_test_001', 'Metadata-Driven-Pipeline', 'PENDING')
        """)
        self.connection.commit()

        # 2. Actively run your orchestrator logic using the in-memory database connection
        status = orchestrator.run_pipeline("run_test_001", db_conn=self.connection)
        
        # Verify the pipeline engine successfully updates and completes as SUCCESS
        self.assertEqual(status, "SUCCESS")

        # 3. Actively verify log values are populated to your logging metrics tables
        self.cursor.execute("SELECT step_name, log_level FROM execution_logs WHERE run_id = 'run_test_001'")
        logs_written = self.cursor.fetchall()

        # Assert that your logic populated multiple detailed logging footprint rows
        self.assertTrue(len(logs_written) >= 3)
        
        # Verify that the initialization and cleanup steps were tracked explicitly
        steps = [log[0] for log in logs_written]
        self.assertIn("INITIALIZATION", steps)
        self.assertIn("CLEANUP", steps)

if __name__ == "__main__":
    unittest.main()
