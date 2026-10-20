import csv
import io
from typing import List
from app.core.interfaces.repositories import IAssessmentRepository

class ExportDatasetUseCase:
    """
    Use Case: Mengonversi seluruh data responden yang terkumpul di WebPBL
    menjadi format CSV standar untuk bahan training/evaluasi tim MachineLearningPBL.
    """

    def __init__(self, repository: IAssessmentRepository):
        self.repository = repository

    def execute(self) -> str:
        records = self.repository.find_all()
        
        output = io.StringIO()
        writer = csv.writer(output)

        # Header kolom dataset primer
        writer.writerow([
            "id",
            "respondent_name",
            "role_division",
            "work_hours",
            "sleep_hours",
            "stress_level",
            "workload_feeling",
            "physical_fatigue",
            "burnout_score",
            "burnout_level",
            "notes",
            "submitted_at"
        ])

        for item in records:
            writer.writerow([
                item.id,
                item.full_name,
                item.role,
                item.work_hours,
                item.sleep_hours,
                item.stress_level,
                item.workload_feeling,
                item.physical_fatigue,
                item.burnout_score,
                item.burnout_level,
                item.notes,
                item.created_at
            ])

        return output.getvalue()
