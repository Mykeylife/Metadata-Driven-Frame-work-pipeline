    def execute_task_logic(self, task: Dict[str, Any]) -> bool:
        """Executes data operations, processes KPI transformations, or validates table status."""
        target_table = task.get("target_table")
        step_name = task.get("step_name", "Unknown Step")
        
        if not target_table:
            logger.error("Task definition is missing an explicit 'target_table' parameter mapping.")
            return False

        # --- LIVE DATA QUALITY GATE BREACH BARRIER ---
        self.validator._get_db_connection = lambda: self._get_db_connection()
        if not self.validator.validate_step(task):
            logger.error(f"Quality Gate Breach: Pre-execution validations failed for step '{step_name}' on table '{target_table}'. Stopping execution pipeline loop.")
            return False

        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Verify that the target table exists before attempting operations
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (target_table,))
                if not cursor.fetchone():
                    logger.error(f"Quality Gate Breach: Target table '{target_table}' does not exist in schema.")
                    return False
                
                if target_table == "analytics_kpis":
                    logger.info("Running real data calculation loop for analytics_kpis...")
                    cursor.execute("SELECT username FROM staging_users;")
                    users = cursor.fetchall()
                    
                    if not users:
                        logger.error("Quality Gate Breach: Extraction halted! Source 'staging_users' table has no records.")
                        return False
                        
                    now_str = datetime.now(timezone.utc).isoformat()
                    for user in users:
                        username = user["username"]
                        cursor.execute(
                            "INSERT INTO analytics_kpis (username, username_length, processed_at) VALUES (?, ?, ?);",
                            (username, len(username), now_str)
                        )
                    conn.commit()
                    logger.info(f"Successfully processed metrics for {len(users)} users inside analytics_kpis.")
                
                elif target_table == "summary_metrics":
                    logger.info("Running aggregation calculation engine for summary_metrics...")
                    cursor.execute("SELECT MAX(username_length) as max_len FROM analytics_kpis;")
                    row = cursor.fetchone()
                    max_length = row["max_len"] if (row and row["max_len"] is not None) else 0
                    
                    now_str = datetime.now(timezone.utc).isoformat()
                    cursor.execute(
                        "INSERT INTO summary_metrics (metric_name, metric_value, calculated_at) VALUES (?, ?, ?);",
                        ("max_username_length", str(max_length), now_str)
                    )
                    conn.commit()
                    logger.info(f"Successfully calculated pipeline aggregations. Max length metric found: {max_length}")

                else:
                    logger.info(f"Initiating operational validation gate for staging table: {target_table}")
                    cursor.execute(f"SELECT 1 FROM {target_table} LIMIT 1;")
                    if not cursor.fetchone():
                        logger.error(f"Quality Gate Breach: Ingestion halted! Table '{target_table}' is empty.")
                        return False
                    
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Database error encountered during logic execution on '{target_table}': {e}.")
            return False
