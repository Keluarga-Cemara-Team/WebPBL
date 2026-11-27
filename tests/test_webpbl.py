import time
import unittest

from app import create_app
from app.core.entities.assessment import RespondentAssessment
from app.core.interfaces.ml_service import IMLPredictorService
from app.core.interfaces.repositories import IAssessmentRepository
from app.core.use_cases.submit_assessment import SubmitAssessmentUseCase
from app.infrastructure.external.http_ml_service import HttpMLPredictorService

VALID_RISK_CATEGORIES = {"Low", "Moderate", "High"}


class InMemoryAssessmentRepository(IAssessmentRepository):
    def __init__(self):
        self.items = []

    def save(self, assessment: RespondentAssessment) -> RespondentAssessment:
        assessment.id = f"TEST-{len(self.items) + 1}"
        self.items.append(assessment)
        return assessment

    def find_all(self):
        return list(reversed(self.items))

    def find_by_id(self, assessment_id):
        for item in self.items:
            if item.id == assessment_id:
                return item
        return None

    def delete(self, assessment_id) -> bool:
        before = len(self.items)
        self.items = [i for i in self.items if i.id != assessment_id]
        return len(self.items) < before

    def bulk_save(self, assessments) -> int:
        for a in assessments:
            self.save(a)
        return len(assessments)


class DeterministicHeuristicMLService(IMLPredictorService):
    """Adapter ML deterministik menggunakan logika fallback resmi WebPBL tanpa koneksi eksternal."""

    def predict_burnout(self, features):
        return HttpMLPredictorService._fallback_prediction(features)


class FailingMLService(IMLPredictorService):
    def predict_burnout(self, features):
        raise RuntimeError("Simulated ML API HTTP 500 error")


class TestPMPLValidationAndEntity(unittest.TestCase):
    """TS-DET-03: Validasi data input dan batasan entitas RespondentAssessment."""

    def test_TC_DET_007_008_invalid_or_empty_name_rejected(self):
        entity_empty = RespondentAssessment(full_name="")
        with self.assertRaises(ValueError):
            entity_empty.validate()

        entity_short = RespondentAssessment(full_name="A")
        with self.assertRaises(ValueError):
            entity_short.validate()

    def test_TC_DET_009_invalid_numeric_bounds_rejected(self):
        with self.assertRaises(ValueError):
            RespondentAssessment(full_name="Budi", age=10.0).validate()
        with self.assertRaises(ValueError):
            RespondentAssessment(full_name="Budi", age=120.0).validate()
        with self.assertRaises(ValueError):
            RespondentAssessment(full_name="Budi", work_hours_per_week=150.0).validate()
        with self.assertRaises(ValueError):
            RespondentAssessment(full_name="Budi", sleep_hours=26.0).validate()

    def test_valid_entity_passes_validation_and_serializes(self):
        entity = RespondentAssessment(
            full_name="Anka Reza",
            person_id="PID-123",
            age=22.0,
            work_hours_per_week=40.0,
            sleep_hours=7.5,
        )
        entity.validate()
        data = entity.to_dict()
        self.assertEqual(data["full_name"], "Anka Reza")
        self.assertEqual(data["person_id"], "PID-123")
        self.assertIn("burnout_score", data)
        self.assertIn("burnout_risk", data)


class TestPMPLClassificationAndRecommendation(unittest.TestCase):
    """TS-KLA-01..04 & TS-REK-01..03: Klasifikasi 3 kategori risiko dan rekomendasi sesuai kategori."""

    def setUp(self):
        self.ml = DeterministicHeuristicMLService()

    def test_TC_KLA_01_and_TC_REK_01_output_kategori_rendah(self):
        res = self.ml.predict_burnout(
            {
                "work_hours_per_week": 35.0,
                "sleep_hours": 8.0,
                "anxiety_score": 15.0,
                "depression_score": 10.0,
                "job_satisfaction": 9.0,
                "work_life_balance": 9.0,
                "stress_level": "Low",
                "chronic_stress": "No",
            }
        )
        self.assertEqual(res["burnout_risk"], "Low")
        self.assertEqual(res["mental_health_status"], "Healthy")
        self.assertEqual(res["ai_wellness_recommendation"], "Maintain Healthy Routine")

    def test_TC_KLA_02_and_TC_REK_02_output_kategori_sedang(self):
        res = self.ml.predict_burnout(
            {
                "work_hours_per_week": 55.0,
                "sleep_hours": 5.5,
                "anxiety_score": 55.0,
                "depression_score": 50.0,
                "job_satisfaction": 4.0,
                "work_life_balance": 4.0,
                "stress_level": "Moderate",
                "chronic_stress": "No",
            }
        )
        self.assertEqual(res["burnout_risk"], "Moderate")
        self.assertEqual(res["mental_health_status"], "Needs Attention")
        self.assertIn(
            res["ai_wellness_recommendation"],
            {"Reduce Workload", "Take Regular Breaks", "Practice Mindfulness"},
        )

    def test_TC_KLA_03_and_TC_REK_03_output_kategori_tinggi(self):
        res = self.ml.predict_burnout(
            {
                "work_hours_per_week": 70.0,
                "sleep_hours": 4.0,
                "anxiety_score": 85.0,
                "depression_score": 80.0,
                "job_satisfaction": 2.0,
                "work_life_balance": 2.0,
                "stress_level": "High",
                "chronic_stress": "Yes",
            }
        )
        self.assertEqual(res["burnout_risk"], "High")
        self.assertEqual(res["mental_health_status"], "Critical")
        self.assertIn(
            res["ai_wellness_recommendation"],
            {"Seek Professional Support", "Reduce Workload"},
        )

    def test_TC_KLA_04_and_TC_DET_003_ten_random_variations_within_3_categories(self):
        samples = [
            {"work_hours_per_week": 20 + i * 7, "sleep_hours": max(3.5, 9.0 - i * 0.5),
             "anxiety_score": 10 + i * 9, "depression_score": 10 + i * 8,
             "job_satisfaction": max(1, 10 - i), "work_life_balance": max(1, 10 - i),
             "stress_level": ["Low", "Moderate", "High"][i % 3],
             "chronic_stress": "Yes" if i >= 6 else "No"}
            for i in range(10)
        ]
        for sample in samples:
            res = self.ml.predict_burnout(sample)
            self.assertIn(res["burnout_risk"], VALID_RISK_CATEGORIES)
            self.assertTrue(0.0 <= res["burnout_score"] <= 100.0)
            self.assertTrue(len(res["ai_wellness_recommendation"]) > 0)


class TestPMPLDetectionAndFallback(unittest.TestCase):
    """TS-DET-01, TS-DET-02, TS-HAS-03: Eksekusi use case, fallback saat koneksi terputus, dan penyimpanan riwayat."""

    def test_TC_DET_004_005_ml_service_unreachable_graceful_fallback(self):
        service = HttpMLPredictorService("http://127.0.0.1:59999/predict")
        res = service.predict_burnout(
            {
                "work_hours_per_week": 65,
                "sleep_hours": 4.5,
                "stress_level": "High",
                "chronic_stress": "Yes",
            }
        )
        self.assertTrue(res["is_simulation"])
        self.assertIn(res["burnout_risk"], VALID_RISK_CATEGORIES)

    def test_TC_HAS_006_007_saved_to_repository_and_latest_first(self):
        repo = InMemoryAssessmentRepository()
        use_case = SubmitAssessmentUseCase(repo, DeterministicHeuristicMLService())

        first, _ = use_case.execute(
            {"person_id": "PID-01", "full_name": "Responden Pertama", "stress_level": "Low", "sleep_hours": 8.0}
        )
        second, _ = use_case.execute(
            {"person_id": "PID-02", "full_name": "Responden Terbaru", "stress_level": "High", "sleep_hours": 4.5}
        )

        self.assertIsNotNone(repo.find_by_id(first.id))
        self.assertIsNotNone(repo.find_by_id(second.id))
        history = repo.find_all()
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0].id, second.id)


class TestPMPLWebEndpointsAndPerformance(unittest.TestCase):
    """TS-DET-01, TS-DET-02, TS-DET-03, TS-DET-04, TS-PERF-01, TS-PERF-02 pada Flask API."""

    def setUp(self):
        self.app = create_app("development")
        self.repo = InMemoryAssessmentRepository()
        self.app.assessment_repository = self.repo
        self.app.db_engine_name = "In-Memory Test Repository"
        self.app.ml_service = DeterministicHeuristicMLService()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_healthz_and_landing_page(self):
        resp_health = self.client.get("/healthz")
        self.assertEqual(resp_health.status_code, 200)
        self.assertEqual(resp_health.get_json()["status"], "healthy")

        resp_home = self.client.get("/")
        self.assertEqual(resp_home.status_code, 200)

    def test_TC_DET_001_002_api_predict_valid_payload_returns_201(self):
        resp = self.client.post(
            "/assessment/api/predict",
            json={
                "person_id": "PID-CI-1",
                "full_name": "Tester CI",
                "age": 22,
                "sleep_hours": 5.0,
                "work_hours_per_week": 60,
                "screen_time_hours": 9.0,
                "stress_level": "High",
                "chronic_stress": "Yes",
            },
        )
        self.assertEqual(resp.status_code, 201)
        body = resp.get_json()
        self.assertEqual(body["status"], "success")
        self.assertEqual(body["data"]["full_name"], "Tester CI")
        self.assertIn(body["evaluation"]["burnout_risk"], VALID_RISK_CATEGORIES)

    def test_TC_DET_007_008_009_api_predict_invalid_payload_returns_400(self):
        resp = self.client.post(
            "/assessment/api/predict",
            json={"full_name": "X", "age": 5},
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.get_json()["status"], "error")

    def test_TC_DET_006_api_error_when_ml_service_crashes(self):
        self.app.ml_service = FailingMLService()
        self.app.config["TESTING"] = False
        self.app.config["DEBUG"] = False
        self.app.config["PROPAGATE_EXCEPTIONS"] = False
        client = self.app.test_client()
        resp = client.post(
            "/assessment/api/predict",
            json={"full_name": "Tester Error", "age": 23, "sleep_hours": 6.0},
        )
        self.assertEqual(resp.status_code, 500)

    def test_TC_DET_010_and_TC_DET_011_performance_under_3s_and_10x_stability(self):
        payload = {
            "person_id": "PID-PERF",
            "full_name": "Stabilitas CI",
            "age": 21,
            "work_hours_per_week": 48,
            "sleep_hours": 6.0,
            "screen_time_hours": 8.0,
            "stress_level": "Moderate",
            "chronic_stress": "No",
        }
        observed_risks = []
        for _ in range(10):
            t0 = time.perf_counter()
            resp = self.client.post("/assessment/api/predict", json=payload)
            elapsed = time.perf_counter() - t0

            self.assertEqual(resp.status_code, 201)
            self.assertLessEqual(elapsed, 3.0, f"Respons melebihi 3 detik: {elapsed:.3f}s")
            body = resp.get_json()
            risk = body["evaluation"]["burnout_risk"]
            self.assertIn(risk, VALID_RISK_CATEGORIES)
            observed_risks.append(risk)

        # Seluruh 10 percobaan dengan input identik harus menghasilkan kategori konsisten
        self.assertEqual(len(set(observed_risks)), 1)


if __name__ == "__main__":
    unittest.main()
