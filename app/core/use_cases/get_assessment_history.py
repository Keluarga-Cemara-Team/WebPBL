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
        
        # Hitung jumlah risiko tinggi (mendukung 'High', 'Critical', atau 'Tinggi')
        high_risk_count = 0
        for a in assessments:
            risk = str(getattr(a, "burnout_risk", "") or getattr(a, "burnout_level", "") or "")
            if any(term in risk for term in ("High", "Critical", "Tinggi")):
                high_risk_count += 1

        return {
            "assessments": [a.to_dict() for a in assessments],
            "metrics": {
                "total_respondents": total,
                "avg_burnout_score": avg_score,
                "high_risk_count": high_risk_count
            }
        }
