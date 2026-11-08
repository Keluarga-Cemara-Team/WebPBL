import sqlite3
from datetime import datetime
from typing import List, Optional, Any
from app.core.entities.assessment import RespondentAssessment
from app.core.interfaces.repositories import IAssessmentRepository
from app.infrastructure.db.sqlite_client import SQLiteClient

class SQLiteAssessmentRepository(IAssessmentRepository):
    """
    Adapter Repository: Mengimplementasikan IAssessmentRepository
    menggunakan SQLite database lokal dengan kompatibilitas skema lama & baru.
    """

    def __init__(self, db_client: SQLiteClient):
        self.db_client = db_client

    def save(self, assessment: RespondentAssessment) -> RespondentAssessment:
        query = """
            INSERT INTO assessments (
                full_name, role, work_hours, sleep_hours,
                stress_level, workload_feeling, physical_fatigue,
                notes, burnout_score, burnout_level, recommendation
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        # Konversi level stres kategori string ke integer (skala 1-5) untuk SQLite
        raw_stress = assessment.stress_level
        if isinstance(raw_stress, (int, float)):
            stress_int = int(raw_stress)
        elif str(raw_stress).lower() == "high":
            stress_int = 5
        elif str(raw_stress).lower() == "moderate":
            stress_int = 3
        else:
            stress_int = 1

        work_hours = getattr(assessment, "work_hours", None) or getattr(assessment, "work_hours_per_week", 40.0)

        params = (
            assessment.full_name,
            assessment.role,
            work_hours,
            assessment.sleep_hours,
            stress_int,
            getattr(assessment, "workload_feeling", 3),
            getattr(assessment, "physical_fatigue", 3),
            assessment.notes or "",
            assessment.burnout_score,
            assessment.burnout_level,
            assessment.recommendation
        )

        with self.db_client.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            assessment.id = cursor.lastrowid
            if not assessment.person_id:
                assessment.person_id = f"PID-{assessment.id:04d}"

        return assessment

    def find_all(self) -> List[RespondentAssessment]:
        query = "SELECT * FROM assessments ORDER BY id DESC"
        results: List[RespondentAssessment] = []

        with self.db_client.get_connection() as conn:
            cursor = conn.cursor()
            rows = cursor.execute(query).fetchall()

            for row in rows:
                results.append(self._row_to_entity(row))

        return results

    def find_by_id(self, assessment_id: Any) -> Optional[RespondentAssessment]:
        query = "SELECT * FROM assessments WHERE id = ?"
        try:
            aid = int(assessment_id)
        except (ValueError, TypeError):
            aid = assessment_id

        with self.db_client.get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(query, (aid,)).fetchone()
            if row:
                return self._row_to_entity(row)
        return None

    def delete(self, assessment_id: Any) -> bool:
        query = "DELETE FROM assessments WHERE id = ?"
        try:
            aid = int(assessment_id)
        except (ValueError, TypeError):
            aid = assessment_id

        with self.db_client.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (aid,))
            conn.commit()
            return cursor.rowcount > 0

    @staticmethod
    def _row_to_entity(row: sqlite3.Row) -> RespondentAssessment:
        keys = row.keys()

        # Format created_at
        raw_created_at = row["created_at"] if "created_at" in keys else None
        created_at_dt = datetime.now()
        if isinstance(raw_created_at, datetime):
            created_at_dt = raw_created_at
        elif isinstance(raw_created_at, str) and raw_created_at:
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
                try:
                    created_at_dt = datetime.strptime(raw_created_at, fmt)
                    break
                except ValueError:
                    pass

        # Mapping role / occupation
        occupation = str(row["role"] if "role" in keys and row["role"] is not None else row.get("occupation", "Software Engineer"))

        # Mapping jam kerja
        raw_work = float(row["work_hours"]) if "work_hours" in keys and row["work_hours"] is not None else float(row.get("work_hours_per_week", 40.0))
        # Jika nilai jam kerja <= 16 (misal input jam harian lama 8h, 9h), sesuaikan ke jam kerja mingguan
        work_hours_per_week = raw_work * 5.0 if raw_work <= 16.0 else raw_work

        # Mapping stress_level (SQLite lama menyimpan int 1-5)
        raw_stress = row["stress_level"] if "stress_level" in keys else "Moderate"
        if isinstance(raw_stress, (int, float)):
            stress_level = "High" if raw_stress >= 4 else ("Moderate" if raw_stress == 3 else "Low")
        else:
            stress_level = str(raw_stress)

        # Mapping burnout risk / level
        raw_risk = str(row["burnout_level"] if "burnout_level" in keys and row["burnout_level"] is not None else row.get("burnout_risk", "Moderate"))
        if any(term in raw_risk for term in ("Tinggi", "High", "Critical")):
            burnout_risk = "High"
            mental_status = "Critical"
        elif any(term in raw_risk for term in ("Rendah", "Low", "Healthy")):
            burnout_risk = "Low"
            mental_status = "Healthy"
        else:
            burnout_risk = "Moderate"
            mental_status = "Needs Attention"

        recommendation = str(row["recommendation"] if "recommendation" in keys and row["recommendation"] is not None else row.get("ai_wellness_recommendation", "Maintain Healthy Routine"))

        row_id = row["id"] if "id" in keys else None
        person_id = f"PID-{row_id:04d}" if row_id is not None else None

        return RespondentAssessment(
            id=row_id,
            person_id=person_id,
            full_name=str(row["full_name"]) if "full_name" in keys and row["full_name"] is not None else "Responden",
            occupation=occupation,
            work_hours_per_week=work_hours_per_week,
            sleep_hours=float(row["sleep_hours"]) if "sleep_hours" in keys and row["sleep_hours"] is not None else 7.0,
            stress_level=stress_level,
            notes=str(row["notes"] or "") if "notes" in keys else "",
            burnout_score=float(row["burnout_score"]) if "burnout_score" in keys and row["burnout_score"] is not None else None,
            burnout_risk=burnout_risk,
            mental_health_status=mental_status,
            ai_wellness_recommendation=recommendation,
            created_at=created_at_dt
        )
