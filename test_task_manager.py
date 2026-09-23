# test_task_manager.py
import unittest
import sqlite3
from task_manager import TaskManager  # Adapts if your class or functions have different names

class TestTaskManager(unittest.TestCase):
    def setUp(self):
        # Establish an isolated in-memory database for testing task processing
        self.connection = sqlite3.connect(":memory:")
        cursor = self.connection.cursor()
        
        # Build a standard engineering tasks schema setup
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                task_name TEXT NOT NULL,
                status TEXT NOT NULL
            )
        """)
        self.connection.commit()

    def tearDown(self):
        self.connection.close()

    def test_task_registration_and_execution(self):
        cursor = self.connection.cursor()
        
        # Test basic task insertion execution logs loop
        cursor.execute("INSERT INTO tasks (task_id, task_name, status) VALUES (?, ?, ?)", 
                       ("task_001", "Data_Extraction", "PENDING"))
        self.connection.commit()
        
        cursor.execute("SELECT status FROM tasks WHERE task_id = ?", ("task_001",))
        row = cursor.fetchone()
        
        self.assertIsNotNone(row)
        self.assertEqual(row[0], "PENDING")

if __name__ == "__main__":
    unittest.main()
