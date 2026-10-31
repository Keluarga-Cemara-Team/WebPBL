import logging
from datetime import datetime
from typing import List, Optional, Any
from app.core.entities.assessment import RespondentAssessment
from app.core.interfaces.repositories import IAssessmentRepository
from app.infrastructure.db.firebase_client import FirebaseClient

logger = logging.getLogger(__name__)

class FirestoreAssessmentRepository(IAssessmentRepository):
    """
    Adapter Repository: Mengimplementasikan IAssessmentRepository
    menggunakan Google Cloud Firestore dengan skema lengkap 40 atribut dataset.
    """

    def __init__(self, firebase_client: FirebaseClient):
        self.db = firebase_client.get_db()
        self.collection_name = "assessments"

    def save(self, assessment: RespondentAssessment) -> RespondentAssessment:
        data = assessment.to_dict()
        data["operator"] = "admin@localhost"

        # Simpan ke koleksi Firestore
        col_ref = self.db.collection(self.collection_name)
        new_doc_ref = col_ref.add(data)[1]  # add() returns (timestamp, doc_ref)
        assessment.id = new_doc_ref.id

        return assessment

    def find_all(self) -> List[RespondentAssessment]:
        results: List[RespondentAssessment] = []
        col_ref = self.db.collection(self.collection_name)

        docs = col_ref.stream()

        for doc in docs:
            d = doc.to_dict()
            results.append(self._doc_to_entity(doc.id, d))

        # Urutkan berdasarkan created_at descending di memori
        results.sort(key=lambda x: str(x.created_at), reverse=True)
        return results

    def find_by_id(self, assessment_id: Any) -> Optional[RespondentAssessment]:
        doc_ref = self.db.collection(self.collection_name).document(str(assessment_id))
        doc = doc_ref.get()
        if doc.exists:
            return self._doc_to_entity(doc.id, doc.to_dict())
        return None

    @staticmethod
    def _doc_to_entity(doc_id: str, data: dict) -> RespondentAssessment:
        raw_created_at = data.get("created_at")
        created_at_dt = datetime.now()
        if isinstance(raw_created_at, datetime):
            created_at_dt = raw_created_at
        elif isinstance(raw_created_at, str) and raw_created_at:
            try:
                created_at_dt = datetime.strptime(raw_created_at, "%Y-%m-%d %H:%M:%S")
            except Exception:
                pass

        return RespondentAssessment(
            id=doc_id,
            person_id=str(data.get("person_id") or doc_id),
            full_name=data.get("full_name", "Responden"),
            age=float(data.get("age", 28.0)),
            gender=data.get("gender", "Male"),
            country=data.get("country", "Indonesia"),
            occupation=data.get("occupation") or data.get("role", "Software Engineer"),
            education_level=data.get("education_level", "Bachelor"),
            employment_status=data.get("employment_status", "Employed"),
            monthly_income_usd=float(data.get("monthly_income_usd", 1500.0)),
            remote_work=data.get("remote_work", "Hybrid"),
            work_hours_per_week=float(data.get("work_hours_per_week") or data.get("work_hours", 40.0)),
            job_satisfaction=float(data.get("job_satisfaction", 6.0)),
            work_life_balance=float(data.get("work_life_balance", 5.0)),
            productivity_score=float(data.get("productivity_score", 65.0)),
            absenteeism_days=int(data.get("absenteeism_days", 2)),
            sleep_hours=float(data.get("sleep_hours", 7.0)),
            sleep_quality=data.get("sleep_quality", "Average"),
            physical_activity_hours=float(data.get("physical_activity_hours", 4.0)),
            exercise_frequency=data.get("exercise_frequency", "Weekly"),
            meditation_minutes=float(data.get("meditation_minutes", 10.0)),
            screen_time_hours=float(data.get("screen_time_hours", 8.0)),
            social_media_hours=float(data.get("social_media_hours", 2.5)),
            gaming_hours=float(data.get("gaming_hours", 1.0)),
            coffee_cups_per_day=int(data.get("coffee_cups_per_day", 2)),
            alcohol_consumption=data.get("alcohol_consumption", "No"),
            smoking=data.get("smoking", "No"),
            healthy_diet=data.get("healthy_diet", "Yes"),
            stress_level=str(data.get("stress_level", "Moderate")),
            chronic_stress=data.get("chronic_stress", "No"),
            anxiety_score=float(data.get("anxiety_score", 35.0)),
            depression_score=float(data.get("depression_score", 30.0)),
            mood_score=float(data.get("mood_score", 60.0)),
            emotional_stability=float(data.get("emotional_stability", 60.0)),
            family_history_mental_illness=data.get("family_history_mental_illness", "No"),
            therapy_attendance=data.get("therapy_attendance", "No"),
            support_system=data.get("support_system", "Good"),
            life_satisfaction=float(data.get("life_satisfaction", 6.0)),
            notes=data.get("notes", ""),
            burnout_score=float(data["burnout_score"]) if data.get("burnout_score") is not None else None,
            burnout_risk=data.get("burnout_risk") or data.get("burnout_level", "Moderate"),
            mental_health_status=data.get("mental_health_status", "Needs Attention"),
            ai_wellness_recommendation=data.get("ai_wellness_recommendation") or data.get("recommendation", "Take Regular Breaks"),
            created_at=created_at_dt
        )
