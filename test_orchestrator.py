# test_orchestrator.py
import unittest
import sqlite3
from datetime import datetime
from orchestrator import PipelineOrchestrator, run_pipeline
from models import PipelineRun, PipelineExecutionError

class TestMetadataPipelineOrchestrator(unittest.TestCase):
    def setUp(self):
        # Create an clean in-memory database configuration for isolated test runs
        self.connection = sqlite3.connect(":memory:")
        self.orchestrator = PipelineOrchestrator(db_conn=self.connection)
        
        # Explicitly build the modern table structures required by the model validations
        cursor = self.connection.cursor()
        cursor.execute("""
            CREATE TABLE pipeline_metadata (
                pipeline_name TEXT PRIMARY KEY,
                is_active INTEGER DEFAULT 1
            )
        """)
        cursor.execute("""
            CREATE TABLE execution_logs (
                run_id TEXT PRIMARY KEY,
                pipeline_name TEXT NOT NULL,
                status TEXT NOT NULL,
                started_at TEXT NOT NULL,
                ended_at TEXT
            )
        """)
        self.connection.commit()

    def tearDown(self):
        self.connection.close()

    def test_orchestrator_execution(self):
        # Seed the metadata table correctly
        cursor = self.connection.cursor()
        cursor.execute("INSERT INTO pipeline_metadata (pipeline_name, is_active) VALUES (?, 1)", 
                       ("Metadata-Driven-Pipeline",))
        self.connection.commit()

        # Run the pipeline test
        result = self.orchestrator.run_pipeline("run_test_001", "Metadata-Driven-Pipeline")
        
        # Verify both data structures are accurately populated
        self.assertIsInstance(result, PipelineRun)
        self.assertEqual(result.status, "SUCCESS")
        self.assertEqual(result.run_id, "run_test_001")
        
        # Assert database state validation logic passes properly
        self.orchestrator.validate_execution_logs("run_test_001")

    def test_inactive_pipeline_throws_error(self):
        # Seed an explicitly disabled pipeline tracking configuration rule
        cursor = self.connection.cursor()
        cursor.execute("INSERT INTO pipeline_metadata (pipeline_name, is_active) VALUES (?, 0)", 
                       ("Disabled-Pipeline",))
        self.connection.commit()

        # Assert that our custom typed validation exception triggers correctly
        with self.assertRaises(PipelineExecutionError):
            self.orchestrator.run_pipeline("run_test_002", "Disabled-Pipeline")

if __name__ == "__main__":
    unittest.main()
