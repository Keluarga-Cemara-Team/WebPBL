import sqlite3
import os
from pathlib import Path

class SQLiteClient:
    """
    Infrastruktur Database SQLite sederhana & handal.
    Menyimpan database di direktori data/antiburnout.db.
    """

    def __init__(self, db_path: Path):
        self.db_path = db_path
        os.makedirs(self.db_path.parent, exist_ok=True)
        self._init_tables()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self) -> None:
        """Membuat tabel jika belum ada"""
        with self.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS assessments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    work_hours REAL NOT NULL,
                    sleep_hours REAL NOT NULL,
                    stress_level INTEGER NOT NULL,
                    workload_feeling INTEGER NOT NULL,
                    physical_fatigue INTEGER NOT NULL,
                    notes TEXT,
                    burnout_score REAL,
                    burnout_level TEXT,
                    recommendation TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
