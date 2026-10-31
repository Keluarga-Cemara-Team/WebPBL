from typing import Dict, Any, Tuple
from app.core.entities.assessment import RespondentAssessment
from app.core.interfaces.repositories import IAssessmentRepository
from app.core.interfaces.ml_service import IMLPredictorService

class SubmitAssessmentUseCase:
    """
    Use Case: Memproses input form dataset primer sesuai 40 kolom dataset,
    mengevaluasi melalui ML, dan menyimpan ke repository database.
    """

    def __init__(self, repository: IAssessmentRepository, ml_service: IMLPredictorService):
        self.repository = repository
        self.ml_service = ml_service

    def execute(self, raw: Dict[str, Any]) -> Tuple[RespondentAssessment, Dict[str, Any]]:
        # Helper untuk parsing float & int aman
        def _f(key, default):
            try:
                val = raw.get(key)
                return float(val) if val not in (None, "") else default
            except (ValueError, TypeError):
                return default

        def _i(key, default):
            try:
                val = raw.get(key)
                return int(val) if val not in (None, "") else default
            except (ValueError, TypeError):
                return default

        # 1. Instansiasi Domain Entity dengan atribut lengkap dataset
        assessment = RespondentAssessment(
            person_id=str(raw.get("person_id") or "").strip() or None,
            full_name=str(raw.get("full_name") or "Responden").strip(),
            age=_f("age", 28.0),
            gender=str(raw.get("gender") or "Male"),
            country=str(raw.get("country") or "Indonesia"),
            occupation=str(raw.get("occupation") or raw.get("role") or "Software Engineer"),
            education_level=str(raw.get("education_level") or "Bachelor"),
            employment_status=str(raw.get("employment_status") or "Employed"),
            monthly_income_usd=_f("monthly_income_usd", 1500.0),
            remote_work=str(raw.get("remote_work") or "Hybrid"),
            work_hours_per_week=_f("work_hours_per_week", _f("work_hours", 40.0)),
            job_satisfaction=_f("job_satisfaction", 6.0),
            work_life_balance=_f("work_life_balance", 5.0),
            productivity_score=_f("productivity_score", 65.0),
            absenteeism_days=_i("absenteeism_days", 2),
            sleep_hours=_f("sleep_hours", 7.0),
            sleep_quality=str(raw.get("sleep_quality") or "Average"),
            physical_activity_hours=_f("physical_activity_hours", 4.0),
            exercise_frequency=str(raw.get("exercise_frequency") or "Weekly"),
            meditation_minutes=_f("meditation_minutes", 10.0),
            screen_time_hours=_f("screen_time_hours", 8.0),
            social_media_hours=_f("social_media_hours", 2.5),
            gaming_hours=_f("gaming_hours", 1.0),
            coffee_cups_per_day=_i("coffee_cups_per_day", 2),
            alcohol_consumption=str(raw.get("alcohol_consumption") or "No"),
            smoking=str(raw.get("smoking") or "No"),
            healthy_diet=str(raw.get("healthy_diet") or "Yes"),
            stress_level=str(raw.get("stress_level") or "Moderate"),
            chronic_stress=str(raw.get("chronic_stress") or "No"),
            anxiety_score=_f("anxiety_score", 35.0),
            depression_score=_f("depression_score", 30.0),
            mood_score=_f("mood_score", 60.0),
            emotional_stability=_f("emotional_stability", 60.0),
            family_history_mental_illness=str(raw.get("family_history_mental_illness") or "No"),
            therapy_attendance=str(raw.get("therapy_attendance") or "No"),
            support_system=str(raw.get("support_system") or "Good"),
            life_satisfaction=_f("life_satisfaction", 6.0),
            notes=str(raw.get("notes") or "").strip()
        )

        # 2. Validasi Domain Rules
        assessment.validate()

        # 3. Minta Prediksi dari ML Service (MachineLearningPBL)
        features_payload = assessment.to_dict()
        ml_result = self.ml_service.predict_burnout(features_payload)

        # 4. Update Entity dengan Hasil Target ML
        assessment.burnout_score = float(ml_result.get("burnout_score", 0.0))
        assessment.burnout_risk = str(ml_result.get("burnout_risk") or ml_result.get("burnout_level", "Moderate"))
        assessment.mental_health_status = str(ml_result.get("mental_health_status") or "Needs Attention")
        assessment.ai_wellness_recommendation = str(ml_result.get("ai_wellness_recommendation") or ml_result.get("recommendation", "Take Regular Breaks"))

        # 5. Persist ke Database (Firestore / SQLite)
        saved_assessment = self.repository.save(assessment)

        return saved_assessment, ml_result
