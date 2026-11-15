from typing import Dict, Any, Tuple
from app.core.entities.assessment import RespondentAssessment
from app.core.interfaces.repositories import IAssessmentRepository
from app.core.interfaces.ml_service import IMLPredictorService

class UpdateAssessmentUseCase:
    """
    Use Case: Memperbarui record dataset responden yang sudah ada di database,
    menjalankan validasi aturan domain, dan secara otomatis (atau sesuai opsi)
    mengkalkulasi ulang skor burnout melalui Machine Learning.
    """

    def __init__(self, repository: IAssessmentRepository, ml_service: IMLPredictorService):
        self.repository = repository
        self.ml_service = ml_service

    def execute(
        self,
        assessment_id: Any,
        raw: Dict[str, Any],
        recalculate_ml: bool = True
    ) -> Tuple[RespondentAssessment, Dict[str, Any]]:
        # 1. Cari record yang akan diperbarui
        existing = self.repository.find_by_id(assessment_id)
        if not existing:
            raise ValueError(f"Data responden dengan ID #{assessment_id} tidak ditemukan.")

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

        # 2. Update atribut dari input form
        existing.person_id = str(raw.get("person_id") or existing.person_id or "").strip() or None
        existing.full_name = str(raw.get("full_name") or existing.full_name or "Responden").strip()
        existing.age = _f("age", existing.age)
        existing.gender = str(raw.get("gender") or existing.gender)
        existing.country = str(raw.get("country") or existing.country)
        existing.occupation = str(raw.get("occupation") or raw.get("role") or existing.occupation)
        existing.education_level = str(raw.get("education_level") or existing.education_level)
        existing.employment_status = str(raw.get("employment_status") or existing.employment_status)
        existing.monthly_income_usd = _f("monthly_income_usd", existing.monthly_income_usd)
        existing.remote_work = str(raw.get("remote_work") or existing.remote_work)
        existing.work_hours_per_week = _f("work_hours_per_week", _f("work_hours", existing.work_hours_per_week))
        existing.job_satisfaction = _f("job_satisfaction", existing.job_satisfaction)
        existing.work_life_balance = _f("work_life_balance", existing.work_life_balance)
        existing.productivity_score = _f("productivity_score", existing.productivity_score)
        existing.absenteeism_days = _i("absenteeism_days", existing.absenteeism_days)
        existing.sleep_hours = _f("sleep_hours", existing.sleep_hours)
        existing.sleep_quality = str(raw.get("sleep_quality") or existing.sleep_quality)
        existing.physical_activity_hours = _f("physical_activity_hours", existing.physical_activity_hours)
        existing.exercise_frequency = str(raw.get("exercise_frequency") or existing.exercise_frequency)
        existing.meditation_minutes = _f("meditation_minutes", existing.meditation_minutes)
        existing.screen_time_hours = _f("screen_time_hours", existing.screen_time_hours)
        existing.social_media_hours = _f("social_media_hours", existing.social_media_hours)
        existing.gaming_hours = _f("gaming_hours", existing.gaming_hours)
        existing.coffee_cups_per_day = _i("coffee_cups_per_day", existing.coffee_cups_per_day)
        existing.alcohol_consumption = str(raw.get("alcohol_consumption") or existing.alcohol_consumption)
        existing.smoking = str(raw.get("smoking") or existing.smoking)
        existing.healthy_diet = str(raw.get("healthy_diet") or existing.healthy_diet)
        existing.stress_level = str(raw.get("stress_level") or existing.stress_level)
        existing.chronic_stress = str(raw.get("chronic_stress") or existing.chronic_stress)
        existing.anxiety_score = _f("anxiety_score", existing.anxiety_score)
        existing.depression_score = _f("depression_score", existing.depression_score)
        existing.mood_score = _f("mood_score", existing.mood_score)
        existing.emotional_stability = _f("emotional_stability", existing.emotional_stability)
        existing.family_history_mental_illness = str(raw.get("family_history_mental_illness") or existing.family_history_mental_illness)
        existing.therapy_attendance = str(raw.get("therapy_attendance") or existing.therapy_attendance)
        existing.support_system = str(raw.get("support_system") or existing.support_system)
        existing.life_satisfaction = _f("life_satisfaction", existing.life_satisfaction)
        existing.notes = str(raw.get("notes") or "").strip()

        # 3. Validasi aturan domain
        existing.validate()

        ml_result: Dict[str, Any] = {}
        # 4. Evaluasi ulang model ML jika diminta
        if recalculate_ml:
            features_payload = existing.to_dict()
            ml_result = self.ml_service.predict_burnout(features_payload)
            existing.burnout_score = float(ml_result.get("burnout_score", existing.burnout_score or 0.0))
            existing.burnout_risk = str(ml_result.get("burnout_risk") or ml_result.get("burnout_level") or existing.burnout_risk or "Moderate")
            existing.mental_health_status = str(ml_result.get("mental_health_status") or existing.mental_health_status or "Needs Attention")
            existing.ai_wellness_recommendation = str(ml_result.get("ai_wellness_recommendation") or ml_result.get("recommendation") or existing.ai_wellness_recommendation or "Take Regular Breaks")
        else:
            ml_result = {
                "burnout_score": existing.burnout_score,
                "burnout_risk": existing.burnout_risk,
                "mental_health_status": existing.mental_health_status,
                "ai_wellness_recommendation": existing.ai_wellness_recommendation
            }

        # 5. Simpan pembaruan ke database
        success = self.repository.update(existing)
        if not success:
            raise RuntimeError(f"Gagal memperbarui record #{assessment_id} pada database storage.")

        return existing, ml_result

