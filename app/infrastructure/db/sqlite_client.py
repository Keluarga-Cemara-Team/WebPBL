import sqlite3
import os
from pathlib import Path
from typing import Dict, Any
from werkzeug.security import generate_password_hash

class SQLiteClient:
    """
    Infrastruktur Database SQLite sederhana & handal.
    Menyimpan database di direktori data/antiburnout.db.
    """

    def __init__(self, db_path: Path):
        self.db_path = db_path
        os.makedirs(self.db_path.parent, exist_ok=True)
        self._init_tables()
        self._seed_default_admin()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self) -> None:
        """Membuat tabel assessments dan users jika belum ada"""
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

            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    full_name TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'admin',
                    division TEXT DEFAULT 'Pusat Riset PBL',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()

    def _seed_default_admin(self) -> None:
        """Memastikan akun admin default tersedia untuk login portal"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin' OR username = 'admin'")
            count = cursor.fetchone()[0]
            if count == 0:
                default_password_hash = generate_password_hash("admin123")
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash, full_name, role, division)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    "admin",
                    "admin@antiburnout.com",
                    default_password_hash,
                    "Administrator PBL",
                    "admin",
                    "Pusat Riset PBL"
                ))
                conn.commit()
                print(">> [Database] Akun admin default berhasil di-seed: username='admin', pass='admin123'")

    def inspect_database(self) -> Dict[str, Any]:
        """Memeriksa integritas dan status tabel-tabel di database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = [row[0] for row in cursor.fetchall()]
            
            summary = {
                "db_path": str(self.db_path),
                "tables": {}
            }
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                summary["tables"][table] = count
            
            # Check admin
            cursor.execute("SELECT username, email, role, full_name FROM users WHERE role = 'admin' LIMIT 1")
            admin_row = cursor.fetchone()
            if admin_row:
                summary["default_admin"] = {
                    "username": admin_row["username"],
                    "email": admin_row["email"],
                    "full_name": admin_row["full_name"],
                    "role": admin_row["role"]
                }
            else:
                summary["default_admin"] = None

            return summary
