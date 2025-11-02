import json
import sqlite3
from datetime import datetime
from pathlib import Path
import pandas as pd

class Database:
    def __init__(self, db_path: str = "data_storage/datasets.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS datasets (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                rows INTEGER,
                columns INTEGER
            )
        """)
        conn.commit()
        conn.close()
    
    def save_dataset(self, filename: str, df: pd.DataFrame) -> str:
        import uuid
        dataset_id = str(uuid.uuid4())
        
        # Convert dataframe to JSON for storage
        data_json = df.to_json(orient='records')
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO datasets (id, filename, data, created_at, rows, columns)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (dataset_id, filename, data_json, datetime.now().isoformat(), len(df), len(df.columns)))
        conn.commit()
        conn.close()
        
        return dataset_id
    
    def get_dataset(self, dataset_id: str):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM datasets WHERE id = ?", (dataset_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def get_all_datasets(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, filename, created_at, rows, columns FROM datasets ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]

