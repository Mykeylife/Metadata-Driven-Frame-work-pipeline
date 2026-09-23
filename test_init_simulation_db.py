# test_init_simulation_db.py
import unittest
import sqlite3
import os
from init_simulation_db import init_db

class TestInitSimulationDB(unittest.TestCase):
    def setUp(self) -> None:
        # Define a distinct temporary database path specifically for test execution
        self.test_db_path = "test_simulation_temp.db"
        # Ensure a clean slate before each test run iteration
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def tearDown(self) -> None:
        # Clean up the isolated test database file immediately after execution
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def test_database_initialization_and_idempotency(self) -> None:
        # 1. Run initialization for the first time to create the schema infrastructure
        init_db(db_path=self.test_db_path)
        
        # Verify the physical file asset was generated properly
        self.assertTrue(os.path.exists(self.test_db_path))

        # Inspect table structural properties natively
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        
        # Assert that the execution_logs infrastructure exists correctly
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='execution_logs'")
        self.assertIsNotNone(cursor.fetchone())
        
        # Assert that the pipeline_metadata table exists correctly
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pipeline_metadata'")
        self.assertIsNotNone(cursor.fetchone())
        
        # Assert that the default seed metadata row was inserted properly
        cursor.execute("SELECT is_active FROM pipeline_metadata WHERE pipeline_name = ?", 
                       ('Metadata-Driven-Frame-work-pipeline',))
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], 1)
        
        conn.close()

        # 2. Test Idempotency: Re-running the script must not crash or throw exceptions
        try:
            init_db(db_path=self.test_db_path)
            idempotency_passed = True
        except Exception:
            idempotency_passed = False
            
        self.assertTrue(idempotency_passed, "Database initialization is not idempotent and failed on re-run.")

if __name__ == "__main__":
    unittest.main()
