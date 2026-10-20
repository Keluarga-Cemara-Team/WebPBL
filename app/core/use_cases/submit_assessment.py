from typing import Dict, Any, Tuple
from app.core.entities.assessment import RespondentAssessment
from app.core.interfaces.repositories import IAssessmentRepository
from app.core.interfaces.ml_service import IMLPredictorService

class SubmitAssessmentUseCase:
    """
    Use Case: Memproses input form dataset primer, mengevaluasi melalui ML,
    dan menyimpan rekam jejaknya ke repository database.
    """

    def __init__(self, repository: IAssessmentRepository, ml_service: IMLPredictorService):
        self.repository = repository
        self.ml_service = ml_service

    def execute(self, raw_data: Dict[str, Any]) -> Tuple[RespondentAssessment, Dict[str, Any]]:
        # 1. Instansiasi Domain Entity
        assessment = RespondentAssessment(
            full_name=str(raw_data.get("full_name", "")).strip(),
            role=str(raw_data.get("role", "Umum")).strip(),
            work_hours=float(raw_data.get("work_hours", 8)),
            sleep_hours=float(raw_data.get("sleep_hours", 7)),
            stress_level=int(raw_data.get("stress_level", 3)),
            workload_feeling=int(raw_data.get("workload_feeling", 3)),
            physical_fatigue=int(raw_data.get("physical_fatigue", 3)),
            notes=str(raw_data.get("notes", "")).strip()
        )

        # 2. Validasi Domain Rules
        assessment.validate()

        # 3. Minta Prediksi dari ML Service (MachineLearningPBL)
        features = {
            "work_hours": assessment.work_hours,
            "sleep_hours": assessment.sleep_hours,
            "stress_level": assessment.stress_level,
            "workload_feeling": assessment.workload_feeling,
            "physical_fatigue": assessment.physical_fatigue
        }
        ml_result = self.ml_service.predict_burnout(features)

        # 4. Update Entity dengan Hasil Evaluasi ML
        assessment.burnout_score = float(ml_result.get("burnout_score", 0.0))
        assessment.burnout_level = str(ml_result.get("burnout_level", "Unknown"))
        assessment.recommendation = str(ml_result.get("recommendation", ""))

        # 5. Persist ke Database melalui Repository
        saved_assessment = self.repository.save(assessment)

        return saved_assessment, ml_result
