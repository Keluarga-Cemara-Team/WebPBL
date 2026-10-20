import sqlite3
from datetime import datetime
from typing import List, Optional
from app.core.entities.assessment import RespondentAssessment
from app.core.interfaces.repositories import IAssessmentRepository
from app.infrastructure.db.sqlite_client import SQLiteClient

class SQLiteAssessmentRepository(IAssessmentRepository):
    """
    Adapter Repository: Mengimplementasikan IAssessmentRepository
    menggunakan SQLite database.
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
        params = (
            assessment.full_name,
            assessment.role,
            assessment.work_hours,
            assessment.sleep_hours,
            assessment.stress_level,
            assessment.workload_feeling,
            assessment.physical_fatigue,
            assessment.notes,
            assessment.burnout_score,
            assessment.burnout_level,
            assessment.recommendation
        )

        with self.db_client.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            assessment.id = cursor.lastrowid

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

    def find_by_id(self, assessment_id: int) -> Optional[RespondentAssessment]:
        query = "SELECT * FROM assessments WHERE id = ?"
        with self.db_client.get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(query, (assessment_id,)).fetchone()
            if row:
                return self._row_to_entity(row)
        return None

    @staticmethod
    def _row_to_entity(row: sqlite3.Row) -> RespondentAssessment:
        return RespondentAssessment(
            id=row["id"],
            full_name=row["full_name"],
            role=row["role"],
            work_hours=float(row["work_hours"]),
            sleep_hours=float(row["sleep_hours"]),
            stress_level=int(row["stress_level"]),
            workload_feeling=int(row["workload_feeling"]),
            physical_fatigue=int(row["physical_fatigue"]),
            notes=row["notes"] or "",
            burnout_score=float(row["burnout_score"]) if row["burnout_score"] is not None else None,
            burnout_level=row["burnout_level"],
            recommendation=row["recommendation"],
            created_at=row["created_at"]
        )
