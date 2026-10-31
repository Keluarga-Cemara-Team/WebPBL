from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any, Dict

@dataclass
class RespondentAssessment:
    """
    Domain Entity: Representasi data primer responden dan evaluasi burnout.
    Sesuai persis dengan skema dataset 'mental_health_burnout_prediction_dataset.csv' (40 atribut).
    """
    # Identitas & Demografi
    id: Optional[Any] = None
    person_id: Optional[str] = None
    full_name: str = "Responden"
    age: float = 28.0
    gender: str = "Male"                  # Male, Female, Other
    country: str = "Indonesia"
    occupation: str = "Software Engineer"
    education_level: str = "Bachelor"     # High School, Diploma, Bachelor, Master, PhD
    employment_status: str = "Employed"   # Employed, Self-Employed, Freelancer, Student, Unemployed
    monthly_income_usd: float = 1500.0
    remote_work: str = "Hybrid"           # Yes, No, Hybrid

    # Beban Kerja & Produktivitas
    work_hours_per_week: float = 45.0
    job_satisfaction: float = 6.0         # 1.0 - 10.0
    work_life_balance: float = 5.0        # 1.0 - 10.0
    productivity_score: float = 65.0      # 0.0 - 100.0
    absenteeism_days: int = 2             # 0 - 30 hari

    # Pola Istirahat & Gaya Hidup
    sleep_hours: float = 6.5
    sleep_quality: str = "Average"        # Poor, Average, Good, Excellent
    physical_activity_hours: float = 4.0
    exercise_frequency: str = "Weekly"    # Never, Rarely, Weekly, Daily
    meditation_minutes: float = 10.0
    screen_time_hours: float = 8.0
    social_media_hours: float = 2.5
    gaming_hours: float = 1.0
    coffee_cups_per_day: int = 2
    alcohol_consumption: str = "No"       # Yes, No
    smoking: str = "No"                   # Yes, No
    healthy_diet: str = "Yes"             # Yes, No

    # Kesehatan Mental & Stres
    stress_level: str = "Moderate"        # Low, Moderate, High
    chronic_stress: str = "No"            # Yes, No
    anxiety_score: float = 35.0           # 0.0 - 100.0
    depression_score: float = 30.0        # 0.0 - 100.0
    mood_score: float = 60.0              # 0.0 - 100.0
    emotional_stability: float = 60.0     # 0.0 - 100.0
    family_history_mental_illness: str = "No" # Yes, No
    therapy_attendance: str = "No"        # Yes, No
    support_system: str = "Good"          # Poor, Average, Good, Excellent
    life_satisfaction: float = 6.0        # 1.0 - 10.0
    notes: Optional[str] = ""

    # Hasil Inferensi / Target Machine Learning
    burnout_score: Optional[float] = None # 0 - 100
    burnout_risk: Optional[str] = None    # Low, Moderate, High
    mental_health_status: Optional[str] = None # Healthy, Needs Attention, Critical
    ai_wellness_recommendation: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    # Aliases untuk kompatibilitas ke belakang (Backward Compatibility)
    @property
    def burnout_level(self) -> str:
        return self.burnout_risk or "Moderate"

    @burnout_level.setter
    def burnout_level(self, val: str) -> None:
        self.burnout_risk = val

    @property
    def role(self) -> str:
        return self.occupation

    @role.setter
    def role(self, val: str) -> None:
        self.occupation = val

    @property
    def recommendation(self) -> str:
        return self.ai_wellness_recommendation or "Maintain Healthy Routine"

    @recommendation.setter
    def recommendation(self, val: str) -> None:
        self.ai_wellness_recommendation = val

    def validate(self) -> None:
        """Validasi aturan batas nilai input"""
        if not self.full_name or len(self.full_name.strip()) < 2:
            raise ValueError("Nama / ID responden minimal 2 karakter.")
        if not (15.0 <= self.age <= 100.0):
            raise ValueError("Usia harus berada di antara 15 sampai 100 tahun.")
        if not (0.0 <= self.work_hours_per_week <= 120.0):
            raise ValueError("Jam kerja mingguan harus berada di antara 0 sampai 120 jam/minggu.")
        if not (0.0 <= self.sleep_hours <= 24.0):
            raise ValueError("Jam tidur harus berada di antara 0 sampai 24 jam/hari.")

    def to_dict(self) -> Dict[str, Any]:
        """Konversi entity ke dictionary"""
        return {
            "id": self.id,
            "person_id": self.person_id or str(self.id),
            "full_name": self.full_name,
            "age": self.age,
            "gender": self.gender,
            "country": self.country,
            "occupation": self.occupation,
            "role": self.occupation,
            "education_level": self.education_level,
            "employment_status": self.employment_status,
            "monthly_income_usd": self.monthly_income_usd,
            "remote_work": self.remote_work,
            "work_hours_per_week": self.work_hours_per_week,
            "job_satisfaction": self.job_satisfaction,
            "work_life_balance": self.work_life_balance,
            "productivity_score": self.productivity_score,
            "absenteeism_days": self.absenteeism_days,
            "sleep_hours": self.sleep_hours,
            "sleep_quality": self.sleep_quality,
            "physical_activity_hours": self.physical_activity_hours,
            "exercise_frequency": self.exercise_frequency,
            "meditation_minutes": self.meditation_minutes,
            "screen_time_hours": self.screen_time_hours,
            "social_media_hours": self.social_media_hours,
            "gaming_hours": self.gaming_hours,
            "coffee_cups_per_day": self.coffee_cups_per_day,
            "alcohol_consumption": self.alcohol_consumption,
            "smoking": self.smoking,
            "healthy_diet": self.healthy_diet,
            "stress_level": self.stress_level,
            "chronic_stress": self.chronic_stress,
            "anxiety_score": self.anxiety_score,
            "depression_score": self.depression_score,
            "mood_score": self.mood_score,
            "emotional_stability": self.emotional_stability,
            "family_history_mental_illness": self.family_history_mental_illness,
            "therapy_attendance": self.therapy_attendance,
            "support_system": self.support_system,
            "life_satisfaction": self.life_satisfaction,
            "notes": self.notes or "",
            "burnout_score": self.burnout_score,
            "burnout_risk": self.burnout_risk,
            "burnout_level": self.burnout_risk or "Moderate",
            "mental_health_status": self.mental_health_status,
            "ai_wellness_recommendation": self.ai_wellness_recommendation,
            "recommendation": self.ai_wellness_recommendation or "Maintain Healthy Routine",
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if isinstance(self.created_at, datetime) else str(self.created_at)
        }
