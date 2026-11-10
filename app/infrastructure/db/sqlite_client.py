import sqlite3
import os
from pathlib import Path
from typing import Dict, Any, Union
from werkzeug.security import generate_password_hash

class SQLiteClient:
    """
    Infrastruktur Database SQLite sederhana & handal.
    Menyimpan database di direktori data/antiburnout.db.
    Mendukung skema lengkap 40 kolom dataset burnout dan tabel otentikasi user.
    """

    def __init__(self, db_path: Union[Path, str]):
        self.db_path = Path(db_path)
        os.makedirs(self.db_path.parent, exist_ok=True)
        self._init_tables()
        self._seed_default_admin()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self) -> None:
        """Membuat tabel assessments dan users serta memigrasikan kolom yang belum ada"""
        schema_columns = {
            "person_id": "TEXT",
            "full_name": "TEXT DEFAULT 'Responden'",
            "age": "REAL DEFAULT 28.0",
            "gender": "TEXT DEFAULT 'Male'",
            "country": "TEXT DEFAULT 'Indonesia'",
            "occupation": "TEXT DEFAULT 'Software Engineer'",
            "role": "TEXT DEFAULT 'Software Engineer'",
            "education_level": "TEXT DEFAULT 'Bachelor'",
            "employment_status": "TEXT DEFAULT 'Employed'",
            "monthly_income_usd": "REAL DEFAULT 1500.0",
            "remote_work": "TEXT DEFAULT 'Hybrid'",
            "work_hours": "REAL DEFAULT 40.0",
            "work_hours_per_week": "REAL DEFAULT 40.0",
            "job_satisfaction": "REAL DEFAULT 6.0",
            "work_life_balance": "REAL DEFAULT 5.0",
            "productivity_score": "REAL DEFAULT 65.0",
            "absenteeism_days": "INTEGER DEFAULT 2",
            "sleep_hours": "REAL DEFAULT 7.0",
            "sleep_quality": "TEXT DEFAULT 'Average'",
            "physical_activity_hours": "REAL DEFAULT 4.0",
            "exercise_frequency": "TEXT DEFAULT 'Weekly'",
            "meditation_minutes": "REAL DEFAULT 10.0",
            "screen_time_hours": "REAL DEFAULT 8.0",
            "social_media_hours": "REAL DEFAULT 2.5",
            "gaming_hours": "REAL DEFAULT 1.0",
            "coffee_cups_per_day": "INTEGER DEFAULT 2",
            "alcohol_consumption": "TEXT DEFAULT 'No'",
            "smoking": "TEXT DEFAULT 'No'",
            "healthy_diet": "TEXT DEFAULT 'Yes'",
            "stress_level": "TEXT DEFAULT 'Moderate'",
            "workload_feeling": "INTEGER DEFAULT 3",
            "physical_fatigue": "INTEGER DEFAULT 3",
            "chronic_stress": "TEXT DEFAULT 'No'",
            "anxiety_score": "REAL DEFAULT 35.0",
            "depression_score": "REAL DEFAULT 30.0",
            "mood_score": "REAL DEFAULT 60.0",
            "emotional_stability": "REAL DEFAULT 60.0",
            "family_history_mental_illness": "TEXT DEFAULT 'No'",
            "therapy_attendance": "TEXT DEFAULT 'No'",
            "support_system": "TEXT DEFAULT 'Good'",
            "life_satisfaction": "REAL DEFAULT 6.0",
            "notes": "TEXT DEFAULT ''",
            "burnout_score": "REAL",
            "burnout_level": "TEXT",
            "burnout_risk": "TEXT",
            "mental_health_status": "TEXT",
            "recommendation": "TEXT",
            "ai_wellness_recommendation": "TEXT",
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        }

        with self.get_connection() as conn:
            # 1. Pastikan tabel dasar assessments ada
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

            # 2. Pastikan tabel users ada
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

            # 3. Periksa kolom yang sudah ada dan tambahkan kolom baru jika belum ada
            cursor = conn.cursor()
            existing_columns = {row[1] for row in cursor.execute("PRAGMA table_info(assessments)").fetchall()}

            for col_name, col_def in schema_columns.items():
                if col_name not in existing_columns:
                    try:
                        cursor.execute(f"ALTER TABLE assessments ADD COLUMN {col_name} {col_def}")
                    except Exception:
                        pass
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
