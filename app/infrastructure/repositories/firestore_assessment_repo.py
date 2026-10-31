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
    menggunakan Google Cloud Firestore.
    """

    def __init__(self, firebase_client: FirebaseClient):
        self.db = firebase_client.get_db()
        self.collection_name = "assessments"

    def save(self, assessment: RespondentAssessment) -> RespondentAssessment:
        data = {
            "full_name": assessment.full_name,
            "role": assessment.role,
            "work_hours": float(assessment.work_hours),
            "sleep_hours": float(assessment.sleep_hours),
            "stress_level": int(assessment.stress_level),
            "workload_feeling": int(assessment.workload_feeling),
            "physical_fatigue": int(assessment.physical_fatigue),
            "notes": assessment.notes or "",
            "burnout_score": float(assessment.burnout_score) if assessment.burnout_score is not None else None,
            "burnout_level": assessment.burnout_level,
            "recommendation": assessment.recommendation,
            "created_at": assessment.created_at.strftime("%Y-%m-%d %H:%M:%S") if isinstance(assessment.created_at, datetime) else str(assessment.created_at),
            "operator": "admin@localhost"
        }

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
            full_name=data.get("full_name", "Anonim"),
            role=data.get("role", "Umum"),
            work_hours=float(data.get("work_hours", 8.0)),
            sleep_hours=float(data.get("sleep_hours", 7.0)),
            stress_level=int(data.get("stress_level", 3)),
            workload_feeling=int(data.get("workload_feeling", 3)),
            physical_fatigue=int(data.get("physical_fatigue", 3)),
            notes=data.get("notes", ""),
            burnout_score=float(data["burnout_score"]) if data.get("burnout_score") is not None else None,
            burnout_level=data.get("burnout_level"),
            recommendation=data.get("recommendation"),
            created_at=created_at_dt
        )

