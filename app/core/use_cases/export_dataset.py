import csv
import io
from app.core.interfaces.repositories import IAssessmentRepository

class ExportDatasetUseCase:
    """
    Use Case: Mengekspor seluruh data responden yang terkumpul di WebPBL
    menjadi file CSV standar yang persis sesuai dengan mental_health_burnout_prediction_dataset.csv
    (40 kolom siap pakai untuk MachineLearningPBL).
    """

    def __init__(self, repository: IAssessmentRepository):
        self.repository = repository

    def execute(self) -> str:
        records = self.repository.find_all()

        output = io.StringIO()
        writer = csv.writer(output)

        # 40 Kolom Standar Dataset PBL
        headers = [
            "Person_ID",
            "Age",
            "Gender",
            "Country",
            "Occupation",
            "Education_Level",
            "Employment_Status",
            "Monthly_Income_USD",
            "Work_Hours_Per_Week",
            "Remote_Work",
            "Job_Satisfaction",
            "Work_Life_Balance",
            "Sleep_Hours",
            "Sleep_Quality",
            "Stress_Level",
            "Anxiety_Score",
            "Depression_Score",
            "Mood_Score",
            "Emotional_Stability",
            "Physical_Activity_Hours",
            "Exercise_Frequency",
            "Meditation_Minutes",
            "Screen_Time_Hours",
            "Social_Media_Hours",
            "Gaming_Hours",
            "Coffee_Cups_Per_Day",
            "Alcohol_Consumption",
            "Smoking",
            "Healthy_Diet",
            "Chronic_Stress",
            "Family_History_Mental_Illness",
            "Therapy_Attendance",
            "Support_System",
            "Life_Satisfaction",
            "Productivity_Score",
            "Absenteeism_Days",
            "Burnout_Score",
            "Mental_Health_Status",
            "AI_Wellness_Recommendation",
            "Burnout_Risk"
        ]
        writer.writerow(headers)

        for idx, item in enumerate(records, start=1):
            writer.writerow([
                item.person_id or str(item.id or idx),
                item.age,
                item.gender,
                item.country,
                item.occupation,
                item.education_level,
                item.employment_status,
                item.monthly_income_usd,
                item.work_hours_per_week,
                item.remote_work,
                item.job_satisfaction,
                item.work_life_balance,
                item.sleep_hours,
                item.sleep_quality,
                item.stress_level,
                item.anxiety_score,
                item.depression_score,
                item.mood_score,
                item.emotional_stability,
                item.physical_activity_hours,
                item.exercise_frequency,
                item.meditation_minutes,
                item.screen_time_hours,
                item.social_media_hours,
                item.gaming_hours,
                item.coffee_cups_per_day,
                item.alcohol_consumption,
                item.smoking,
                item.healthy_diet,
                item.chronic_stress,
                item.family_history_mental_illness,
                item.therapy_attendance,
                item.support_system,
                item.life_satisfaction,
                item.productivity_score,
                item.absenteeism_days,
                item.burnout_score,
                item.mental_health_status,
                item.ai_wellness_recommendation,
                item.burnout_risk
            ])

        return output.getvalue()
