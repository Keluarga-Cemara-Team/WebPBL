import unittest
from app import create_app
from app.core.entities.assessment import RespondentAssessment
from app.core.use_cases import GetDashboardAnalyticsUseCase

class MockAssessmentRepository:
    def __init__(self, records=None):
        self.records = records or []

    def find_all(self):
        return self.records

    def find_by_id(self, aid):
        return None

    def save(self, entity):
        return entity

    def update(self, entity):
        return True

    def delete(self, aid):
        return True

    def bulk_save(self, list_items):
        return len(list_items)

class TestDashboardAnalytics(unittest.TestCase):
    def setUp(self):
        self.app = create_app("development")
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_use_case_empty_analytics(self):
        """Uji use case analitik jika dataset kosong"""
        repo = MockAssessmentRepository([])
        use_case = GetDashboardAnalyticsUseCase(repo)
        result = use_case.execute()

        self.assertEqual(result["total_respondents"], 0)
        self.assertEqual(result["avg_burnout_score"], 0.0)
        self.assertEqual(result["high_risk_count"], 0)
        self.assertIn("risk_distribution", result)

    def test_use_case_with_records(self):
        """Uji agregasi metrik dari sekumpulan responden"""
        rec1 = RespondentAssessment(
            full_name="User A",
            burnout_score=80.0,
            burnout_risk="High",
            mental_health_status="Critical",
            work_hours_per_week=50.0,
            sleep_hours=5.0,
            job_satisfaction=4.0
        )
        rec2 = RespondentAssessment(
            full_name="User B",
            burnout_score=30.0,
            burnout_risk="Low",
            mental_health_status="Healthy",
            work_hours_per_week=38.0,
            sleep_hours=8.0,
            job_satisfaction=8.0
        )

        repo = MockAssessmentRepository([rec1, rec2])
        use_case = GetDashboardAnalyticsUseCase(repo)
        res = use_case.execute()

        self.assertEqual(res["total_respondents"], 2)
        self.assertEqual(res["avg_burnout_score"], 55.0)
        self.assertEqual(res["high_risk_count"], 1)
        self.assertEqual(res["high_risk_percentage"], 50.0)
        self.assertEqual(res["avg_work_hours"], 44.0)
        self.assertEqual(res["avg_sleep_hours"], 6.5)
        self.assertEqual(res["risk_distribution"]["data"], [1, 0, 1])

    def test_dashboard_route_contains_kpi_and_charts(self):
        """Uji apakah dashboard utama merender elemen grafik dan KPI setelah login"""
        # Login
        self.client.post("/login", data={
            "identifier": "admin",
            "password": "admin123"
        })

        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        # Periksa kartu KPI & canvas grafik
        self.assertIn(b"Total Responden", res.data)
        self.assertIn(b"Rata-rata Skor Burnout", res.data)
        self.assertIn(b"chart-risk-distribution", res.data)
        self.assertIn(b"chart-work-sleep", res.data)
        self.assertIn(b"chart-mental-health", res.data)
        self.assertIn(b"chart-wellness-pillars", res.data)
        self.assertIn(b"dashboard_charts.js", res.data)

    def test_dashboard_stats_api_endpoint(self):
        """Uji endpoint API /api/dashboard/stats"""
        # Login
        self.client.post("/login", data={
            "identifier": "admin",
            "password": "admin123"
        })

        res = self.client.get("/api/dashboard/stats")
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()
        self.assertEqual(json_data["status"], "success")
        self.assertIn("total_respondents", json_data["data"])
        self.assertIn("risk_distribution", json_data["data"])
        self.assertIn("work_sleep_by_risk", json_data["data"])

if __name__ == "__main__":
    unittest.main()

