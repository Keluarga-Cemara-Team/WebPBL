from typing import List, Dict, Any
from app.core.interfaces.repositories import IAssessmentRepository

class GetAssessmentHistoryUseCase:
    """
    Use Case: Mengambil daftar riwayat input data primer dan ringkasan metrik.
    """

    def __init__(self, repository: IAssessmentRepository):
        self.repository = repository

    def execute(self) -> Dict[str, Any]:
        assessments = self.repository.find_all()
        
        total = len(assessments)
        avg_score = round(sum((a.burnout_score or 0) for a in assessments) / total, 1) if total > 0 else 0
        high_risk_count = sum(1 for a in assessments if "Tinggi" in (a.burnout_level or ""))

        return {
            "assessments": [a.to_dict() for a in assessments],
            "metrics": {
                "total_respondents": total,
                "avg_burnout_score": avg_score,
                "high_risk_count": high_risk_count
            }
        }
