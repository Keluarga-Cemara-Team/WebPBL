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

    def bulk_save(self, assessments: List[RespondentAssessment]) -> int:
        """Menyimpan sekumpulan data responden sekaligus menggunakan executemany (batch insert)"""
        if not assessments:
            return 0

        query = """
            INSERT INTO assessments (
                person_id, full_name, age, gender, country, occupation, role,
                education_level, employment_status, monthly_income_usd, remote_work,
                work_hours, work_hours_per_week, job_satisfaction, work_life_balance,
                productivity_score, absenteeism_days, sleep_hours, sleep_quality,
                physical_activity_hours, exercise_frequency, meditation_minutes,
                screen_time_hours, social_media_hours, gaming_hours, coffee_cups_per_day,
                alcohol_consumption, smoking, healthy_diet, stress_level, workload_feeling,
                physical_fatigue, chronic_stress, anxiety_score, depression_score,
                mood_score, emotional_stability, family_history_mental_illness,
                therapy_attendance, support_system, life_satisfaction, notes,
                burnout_score, burnout_level, burnout_risk, mental_health_status,
                recommendation, ai_wellness_recommendation, created_at
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
        """
        rows = [self._entity_to_db_tuple(a) for a in assessments]

        with self.db_client.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, rows)
            conn.commit()
            return len(rows)

    def _entity_to_db_tuple(self, a: RespondentAssessment) -> tuple:
        """Helper untuk mengubah RespondentAssessment menjadi tuple parameter query"""
        # Format created_at
        if isinstance(a.created_at, datetime):
            c_at = a.created_at.strftime("%Y-%m-%d %H:%M:%S")
        else:
            c_at = str(a.created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        work_hours = getattr(a, "work_hours", None) or getattr(a, "work_hours_per_week", 40.0)

        # Mapping stress_level
        raw_stress = a.stress_level
        stress_str = str(raw_stress)
        if isinstance(raw_stress, (int, float)):
            stress_str = "High" if raw_stress >= 4 else ("Moderate" if raw_stress == 3 else "Low")

        return (
            a.person_id or "",
            a.full_name or "Responden",
            float(a.age or 28.0),
            a.gender or "Male",
            a.country or "Indonesia",
            a.occupation or "Software Engineer",
            a.role or a.occupation or "Software Engineer",
            a.education_level or "Bachelor",
            a.employment_status or "Employed",
            float(a.monthly_income_usd or 1500.0),
            a.remote_work or "Hybrid",
            float(work_hours),
            float(a.work_hours_per_week or 40.0),
            float(a.job_satisfaction or 6.0),
            float(a.work_life_balance or 5.0),
            float(a.productivity_score or 65.0),
            int(a.absenteeism_days or 0),
            float(a.sleep_hours or 7.0),
            a.sleep_quality or "Average",
            float(a.physical_activity_hours or 4.0),
            a.exercise_frequency or "Weekly",
            float(a.meditation_minutes or 10.0),
            float(a.screen_time_hours or 8.0),
            float(a.social_media_hours or 2.5),
            float(a.gaming_hours or 1.0),
            int(a.coffee_cups_per_day or 0),
            a.alcohol_consumption or "No",
            a.smoking or "No",
            a.healthy_diet or "Yes",
            stress_str,
            int(getattr(a, "workload_feeling", 3) or 3),
            int(getattr(a, "physical_fatigue", 3) or 3),
            a.chronic_stress or "No",
            float(a.anxiety_score or 35.0),
            float(a.depression_score or 30.0),
            float(a.mood_score or 60.0),
            float(a.emotional_stability or 60.0),
            a.family_history_mental_illness or "No",
            a.therapy_attendance or "No",
            a.support_system or "Good",
            float(a.life_satisfaction or 6.0),
            a.notes or "",
            float(a.burnout_score) if a.burnout_score is not None else None,
            a.burnout_level or a.burnout_risk or "Moderate",
            a.burnout_risk or "Moderate",
            a.mental_health_status or "Needs Attention",
            a.recommendation or "Maintain Healthy Routine",
            a.ai_wellness_recommendation or "Maintain Healthy Routine",
            c_at
        )

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
        occupation = str(row["occupation"] if "occupation" in keys and row["occupation"] is not None else (row["role"] if "role" in keys and row["role"] is not None else "Software Engineer"))

        # Mapping jam kerja
        raw_work = float(row["work_hours_per_week"]) if "work_hours_per_week" in keys and row["work_hours_per_week"] is not None else (float(row["work_hours"]) if "work_hours" in keys and row["work_hours"] is not None else 40.0)
        # Jika nilai jam kerja <= 16 (misal input jam harian lama 8h, 9h), sesuaikan ke jam kerja mingguan
        work_hours_per_week = raw_work * 5.0 if raw_work <= 16.0 else raw_work

        # Mapping stress_level (SQLite lama menyimpan int 1-5)
        raw_stress = row["stress_level"] if "stress_level" in keys else "Moderate"
        if isinstance(raw_stress, (int, float)):
            stress_level = "High" if raw_stress >= 4 else ("Moderate" if raw_stress == 3 else "Low")
        else:
            stress_level = str(raw_stress)

        # Mapping burnout risk / level
        raw_risk = str(row["burnout_risk"] if "burnout_risk" in keys and row["burnout_risk"] is not None else (row["burnout_level"] if "burnout_level" in keys and row["burnout_level"] is not None else "Moderate"))
        if any(term in raw_risk for term in ("Tinggi", "High", "Critical")):
            burnout_risk = "High"
            default_status = "Critical"
        elif any(term in raw_risk for term in ("Rendah", "Low", "Healthy")):
            burnout_risk = "Low"
            default_status = "Healthy"
        else:
            burnout_risk = "Moderate"
            default_status = "Needs Attention"

        mental_status = str(row["mental_health_status"]) if "mental_health_status" in keys and row["mental_health_status"] is not None else default_status
        recommendation = str(row["ai_wellness_recommendation"] if "ai_wellness_recommendation" in keys and row["ai_wellness_recommendation"] is not None else (row["recommendation"] if "recommendation" in keys and row["recommendation"] is not None else "Maintain Healthy Routine"))

        row_id = row["id"] if "id" in keys else None
        person_id = str(row["person_id"]) if "person_id" in keys and row["person_id"] else (f"PID-{row_id:04d}" if row_id is not None else None)

        return RespondentAssessment(
            id=row_id,
            person_id=person_id,
            full_name=str(row["full_name"]) if "full_name" in keys and row["full_name"] is not None else "Responden",
            age=float(row["age"]) if "age" in keys and row["age"] is not None else 28.0,
            gender=str(row["gender"]) if "gender" in keys and row["gender"] is not None else "Male",
            country=str(row["country"]) if "country" in keys and row["country"] is not None else "Indonesia",
            occupation=occupation,
            education_level=str(row["education_level"]) if "education_level" in keys and row["education_level"] is not None else "Bachelor",
            employment_status=str(row["employment_status"]) if "employment_status" in keys and row["employment_status"] is not None else "Employed",
            monthly_income_usd=float(row["monthly_income_usd"]) if "monthly_income_usd" in keys and row["monthly_income_usd"] is not None else 1500.0,
            remote_work=str(row["remote_work"]) if "remote_work" in keys and row["remote_work"] is not None else "Hybrid",
            work_hours_per_week=work_hours_per_week,
            job_satisfaction=float(row["job_satisfaction"]) if "job_satisfaction" in keys and row["job_satisfaction"] is not None else 6.0,
            work_life_balance=float(row["work_life_balance"]) if "work_life_balance" in keys and row["work_life_balance"] is not None else 5.0,
            productivity_score=float(row["productivity_score"]) if "productivity_score" in keys and row["productivity_score"] is not None else 65.0,
            absenteeism_days=int(row["absenteeism_days"]) if "absenteeism_days" in keys and row["absenteeism_days"] is not None else 2,
            sleep_hours=float(row["sleep_hours"]) if "sleep_hours" in keys and row["sleep_hours"] is not None else 7.0,
            sleep_quality=str(row["sleep_quality"]) if "sleep_quality" in keys and row["sleep_quality"] is not None else "Average",
            physical_activity_hours=float(row["physical_activity_hours"]) if "physical_activity_hours" in keys and row["physical_activity_hours"] is not None else 4.0,
            exercise_frequency=str(row["exercise_frequency"]) if "exercise_frequency" in keys and row["exercise_frequency"] is not None else "Weekly",
            meditation_minutes=float(row["meditation_minutes"]) if "meditation_minutes" in keys and row["meditation_minutes"] is not None else 10.0,
            screen_time_hours=float(row["screen_time_hours"]) if "screen_time_hours" in keys and row["screen_time_hours"] is not None else 8.0,
            social_media_hours=float(row["social_media_hours"]) if "social_media_hours" in keys and row["social_media_hours"] is not None else 2.5,
            gaming_hours=float(row["gaming_hours"]) if "gaming_hours" in keys and row["gaming_hours"] is not None else 1.0,
            coffee_cups_per_day=int(row["coffee_cups_per_day"]) if "coffee_cups_per_day" in keys and row["coffee_cups_per_day"] is not None else 2,
            alcohol_consumption=str(row["alcohol_consumption"]) if "alcohol_consumption" in keys and row["alcohol_consumption"] is not None else "No",
            smoking=str(row["smoking"]) if "smoking" in keys and row["smoking"] is not None else "No",
            healthy_diet=str(row["healthy_diet"]) if "healthy_diet" in keys and row["healthy_diet"] is not None else "Yes",
            stress_level=stress_level,
            chronic_stress=str(row["chronic_stress"]) if "chronic_stress" in keys and row["chronic_stress"] is not None else "No",
            anxiety_score=float(row["anxiety_score"]) if "anxiety_score" in keys and row["anxiety_score"] is not None else 35.0,
            depression_score=float(row["depression_score"]) if "depression_score" in keys and row["depression_score"] is not None else 30.0,
            mood_score=float(row["mood_score"]) if "mood_score" in keys and row["mood_score"] is not None else 60.0,
            emotional_stability=float(row["emotional_stability"]) if "emotional_stability" in keys and row["emotional_stability"] is not None else 60.0,
            family_history_mental_illness=str(row["family_history_mental_illness"]) if "family_history_mental_illness" in keys and row["family_history_mental_illness"] is not None else "No",
            therapy_attendance=str(row["therapy_attendance"]) if "therapy_attendance" in keys and row["therapy_attendance"] is not None else "No",
            support_system=str(row["support_system"]) if "support_system" in keys and row["support_system"] is not None else "Good",
            life_satisfaction=float(row["life_satisfaction"]) if "life_satisfaction" in keys and row["life_satisfaction"] is not None else 6.0,
            notes=str(row["notes"] or "") if "notes" in keys else "",
            burnout_score=float(row["burnout_score"]) if "burnout_score" in keys and row["burnout_score"] is not None else None,
            burnout_risk=burnout_risk,
            mental_health_status=mental_status,
            ai_wellness_recommendation=recommendation,
            created_at=created_at_dt
        )
