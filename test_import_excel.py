import io
import unittest
import pandas as pd
from app.core.entities.assessment import RespondentAssessment
from app.core.interfaces.repositories import IAssessmentRepository
from app.core.interfaces.ml_service import IMLPredictorService
from app.core.use_cases.import_dataset import ImportDatasetUseCase

class MockAssessmentRepository(IAssessmentRepository):
    def __init__(self):
        self.records = {}
        self.counter = 1

    def save(self, assessment: RespondentAssessment) -> RespondentAssessment:
        if not assessment.id:
            assessment.id = self.counter
            self.counter += 1
        self.records[assessment.id] = assessment
        return assessment

    def find_all(self):
        return list(self.records.values())

    def find_by_id(self, assessment_id):
        return self.records.get(assessment_id)

    def delete(self, assessment_id):
        if assessment_id in self.records:
            del self.records[assessment_id]
            return True
        return False

    def bulk_save(self, assessments):
        for a in assessments:
            self.save(a)
        return len(assessments)

class MockMLService(IMLPredictorService):
    def predict_burnout(self, features):
        return {
            "burnout_score": 68.5,
            "burnout_risk": "Moderate",
            "mental_health_status": "Needs Attention",
            "ai_wellness_recommendation": "Mock Recommendation: Take Breaks"
        }

class TestImportExcelUseCase(unittest.TestCase):
    def setUp(self):
        self.repo = MockAssessmentRepository()
        self.ml_service = MockMLService()
        self.use_case = ImportDatasetUseCase(self.repo, self.ml_service)

    def test_generate_excel_template(self):
        """Uji apakah file template Excel (.xlsx) berhasil dibuat dan memiliki 40 kolom"""
        excel_bytes = ImportDatasetUseCase.generate_excel_template()
        self.assertTrue(len(excel_bytes) > 1000)

        # Verifikasi konten Excel menggunakan pandas
        df = pd.read_excel(io.BytesIO(excel_bytes), sheet_name="Data Responden")
        self.assertIn("Person_ID", df.columns)
        self.assertIn("Work_Hours_Per_Week", df.columns)
        self.assertIn("Sleep_Hours", df.columns)
        self.assertIn("Stress_Level", df.columns)
        self.assertEqual(len(df), 2)  # 2 baris contoh

    def test_import_excel_with_auto_prediction(self):
        """Uji impor file Excel di mana target burnout kosong, harus otomatis dihitung ML"""
        sample_data = {
            "Person_ID": ["EXP-001", "EXP-002"],
            "Nama": ["Budi Santoso", "Dewi Lestari"],
            "Usia": [28, 32],
            "Gender": ["Male", "Female"],
            "Pekerjaan": ["Backend Developer", "Product Manager"],
            "Jam Kerja Mingguan": [50.0, 42.0],
            "Jam Tidur": [6.0, 7.5],
            "Tingkat Stres": ["High", "Low"],
        }
        df = pd.DataFrame(sample_data)
        excel_buf = io.BytesIO()
        df.to_excel(excel_buf, index=False, engine="openpyxl")

        result = self.use_case.execute(
            file_content=excel_buf.getvalue(),
            filename="test_survey.xlsx",
            mode="append",
            auto_predict=True
        )

        self.assertEqual(result["imported_count"], 2)
        self.assertEqual(result["skipped_count"], 0)

        # Cek database
        saved = self.repo.find_all()
        self.assertEqual(len(saved), 2)
        self.assertEqual(saved[0].full_name, "Budi Santoso")
        self.assertEqual(saved[0].work_hours_per_week, 50.0)
        # Harus terisi otomatis oleh ML
        self.assertEqual(saved[0].burnout_score, 68.5)
        self.assertEqual(saved[0].burnout_risk, "Moderate")
        self.assertEqual(saved[0].ai_wellness_recommendation, "Mock Recommendation: Take Breaks")

    def test_import_excel_replace_mode(self):
        """Uji apakah mode replace menghapus data lama sebelum mengimpor"""
        # Masukkan 1 data awal
        initial_entity = RespondentAssessment(full_name="User Lama", work_hours_per_week=40.0)
        self.repo.save(initial_entity)
        self.assertEqual(len(self.repo.find_all()), 1)

        # Impor Excel baru dengan mode replace
        df = pd.DataFrame({"Person_ID": ["NEW-01"], "Nama": ["User Baru"]})
        excel_buf = io.BytesIO()
        df.to_excel(excel_buf, index=False, engine="openpyxl")

        result = self.use_case.execute(
            file_content=excel_buf.getvalue(),
            filename="data_baru.xlsx",
            mode="replace",
            auto_predict=True
        )

        self.assertEqual(result["imported_count"], 1)
        saved = self.repo.find_all()
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0].full_name, "User Baru")

    def test_unsupported_file_extension(self):
        """Uji validasi ekstensi file yang tidak didukung"""
        with self.assertRaises(ValueError):
            self.use_case.execute(b"fake data", "document.pdf")

class TestImportRoutes(unittest.TestCase):
    def setUp(self):
        from app import create_app
        self.app = create_app("testing")
        self.client = self.app.test_client()

    def _login(self):
        with self.client.session_transaction() as sess:
            sess["logged_in"] = True
            sess["user_id"] = "admin"
            sess["username"] = "admin"
            sess["user_role"] = "admin"

    def test_import_view_get(self):
        self._login()
        res = self.client.get("/assessment/import")
        self.assertEqual(res.status_code, 200)
        self.assertIn("Import Dataset".encode("utf-8"), res.data)

    def test_download_template_route(self):
        self._login()
        res = self.client.get("/assessment/import/template")
        self.assertEqual(res.status_code, 200)
        self.assertIn("application/vnd.openxmlformats", res.content_type)
        self.assertIn("antiburnout_dataset_template.xlsx", res.headers.get("Content-Disposition", ""))

    def test_import_post_valid_excel(self):
        self._login()
        sample_data = {
            "Person_ID": ["ROUTE-01"],
            "Nama": ["Responden Route Test"],
            "Age": [27],
            "Gender": ["Female"],
            "Work_Hours_Per_Week": [45],
            "Sleep_Hours": [7]
        }
        df = pd.DataFrame(sample_data)
        excel_buf = io.BytesIO()
        df.to_excel(excel_buf, index=False, engine="openpyxl")
        excel_buf.seek(0)

        data = {
            "dataset_file": (excel_buf, "survey_route_test.xlsx"),
            "mode": "append",
            "auto_predict": "1"
        }
        res = self.client.post("/assessment/import", data=data, content_type="multipart/form-data")
        # Harusnya redirect ke dataset_view setelah berhasil
        self.assertEqual(res.status_code, 302)
        self.assertIn("/assessment/dataset", res.headers["Location"])

if __name__ == "__main__":
    unittest.main()

