from collections import Counter
from typing import Dict, Any, List
from app.core.interfaces.repositories import IAssessmentRepository

class GetDashboardAnalyticsUseCase:
    """
    Use Case: Mengagregasi data primer seluruh responden dari repository
    untuk menghasilkan visualisasi statistik, distribusi risiko burnout,
    korelasi jam kerja vs istirahat, serta indikator kesehatan mental di dashboard utama.
    """

    def __init__(self, repository: IAssessmentRepository):
        self.repository = repository

    def execute(self) -> Dict[str, Any]:
        records = self.repository.find_all()
        total = len(records)

        if total == 0:
            return self._empty_analytics()

        # 1. Metrik Utama Ringkas (KPI)
        scores = [r.burnout_score for r in records if r.burnout_score is not None]
        avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0

        work_hours = [float(getattr(r, "work_hours_per_week", None) or getattr(r, "work_hours", 40.0) or 40.0) for r in records]
        avg_work = round(sum(work_hours) / len(work_hours), 1) if work_hours else 0.0

        sleep_hours = [float(r.sleep_hours or 7.0) for r in records]
        avg_sleep = round(sum(sleep_hours) / len(sleep_hours), 1) if sleep_hours else 0.0

        # 2. Distribusi Tingkat Risiko (Burnout Risk)
        risk_counts = {"Low": 0, "Moderate": 0, "High": 0}
        risk_groups: Dict[str, Dict[str, List[float]]] = {
            "Low": {"work": [], "sleep": []},
            "Moderate": {"work": [], "sleep": []},
            "High": {"work": [], "sleep": []}
        }

        for r in records:
            raw_risk = str(getattr(r, "burnout_risk", "") or getattr(r, "burnout_level", "") or "Moderate")
            normalized_risk = "Moderate"
            if any(term in raw_risk for term in ("High", "Critical", "Tinggi")):
                normalized_risk = "High"
            elif any(term in raw_risk for term in ("Low", "Healthy", "Rendah")):
                normalized_risk = "Low"

            risk_counts[normalized_risk] += 1

            # Catat jam kerja dan jam tidur per kelompok risiko
            w = float(getattr(r, "work_hours_per_week", None) or getattr(r, "work_hours", 40.0) or 40.0)
            s = float(r.sleep_hours or 7.0)
            risk_groups[normalized_risk]["work"].append(w)
            risk_groups[normalized_risk]["sleep"].append(s)

        high_risk_count = risk_counts["High"]
        high_risk_pct = round((high_risk_count / total) * 100, 1)

        # 3. Rata-rata Beban Kerja vs Jam Tidur per Kategori Risiko
        work_sleep_by_risk = {}
        for r_name in ("Low", "Moderate", "High"):
            w_list = risk_groups[r_name]["work"]
            s_list = risk_groups[r_name]["sleep"]
            work_sleep_by_risk[r_name] = {
                "avg_work_hours": round(sum(w_list) / len(w_list), 1) if w_list else 0.0,
                "avg_sleep_hours": round(sum(s_list) / len(s_list), 1) if s_list else 0.0
            }

        # 4. Distribusi Status Kesehatan Mental
        mental_counts = {"Healthy": 0, "Needs Attention": 0, "Critical": 0}
        for r in records:
            m_status = str(getattr(r, "mental_health_status", "") or "").strip()
            if "Critical" in m_status:
                mental_counts["Critical"] += 1
            elif "Healthy" in m_status:
                mental_counts["Healthy"] += 1
            else:
                mental_counts["Needs Attention"] += 1

        # 5. Pilar Kesejahteraan & Kepuasan Kerja (Skala 1 - 10 & 0 - 100)
        job_sats = [float(r.job_satisfaction) for r in records if r.job_satisfaction is not None]
        wlb_scores = [float(r.work_life_balance) for r in records if r.work_life_balance is not None]
        prod_scores = [float(r.productivity_score) for r in records if r.productivity_score is not None]
        life_sats = [float(r.life_satisfaction) for r in records if r.life_satisfaction is not None]

        wellness_pillars = {
            "job_satisfaction": round(sum(job_sats) / len(job_sats), 1) if job_sats else 6.0,
            "work_life_balance": round(sum(wlb_scores) / len(wlb_scores), 1) if wlb_scores else 5.5,
            "productivity_score": round(sum(prod_scores) / len(prod_scores), 1) if prod_scores else 65.0,
            "life_satisfaction": round(sum(life_sats) / len(life_sats), 1) if life_sats else 6.0
        }

        # 6. Top 5 Pekerjaan / Profesi Terbanyak
        occupations = [str(r.occupation or r.role or "Other").strip() for r in records if str(r.occupation or r.role or "").strip()]
        top_occupations = [
            {"name": occ, "count": cnt}
            for occ, cnt in Counter(occupations).most_common(5)
        ]

        return {
            "total_respondents": total,
            "avg_burnout_score": avg_score,
            "high_risk_count": high_risk_count,
            "high_risk_percentage": high_risk_pct,
            "avg_work_hours": avg_work,
            "avg_sleep_hours": avg_sleep,
            "risk_distribution": {
                "labels": ["Low Risk (Rendah)", "Moderate Risk (Sedang)", "High Risk (Tinggi)"],
                "data": [risk_counts["Low"], risk_counts["Moderate"], risk_counts["High"]],
                "percentages": [
                    round((risk_counts["Low"] / total) * 100, 1),
                    round((risk_counts["Moderate"] / total) * 100, 1),
                    round((risk_counts["High"] / total) * 100, 1)
                ]
            },
            "work_sleep_by_risk": {
                "labels": ["Low Risk", "Moderate Risk", "High Risk"],
                "work_hours": [
                    work_sleep_by_risk["Low"]["avg_work_hours"],
                    work_sleep_by_risk["Moderate"]["avg_work_hours"],
                    work_sleep_by_risk["High"]["avg_work_hours"]
                ],
                "sleep_hours": [
                    work_sleep_by_risk["Low"]["avg_sleep_hours"],
                    work_sleep_by_risk["Moderate"]["avg_sleep_hours"],
                    work_sleep_by_risk["High"]["avg_sleep_hours"]
                ]
            },
            "mental_health_distribution": {
                "labels": ["Healthy (Prima)", "Needs Attention (Perlu Perhatian)", "Critical (Kritis)"],
                "data": [mental_counts["Healthy"], mental_counts["Needs Attention"], mental_counts["Critical"]]
            },
            "wellness_pillars": wellness_pillars,
            "top_occupations": top_occupations
        }

    def _empty_analytics(self) -> Dict[str, Any]:
        return {
            "total_respondents": 0,
            "avg_burnout_score": 0.0,
            "high_risk_count": 0,
            "high_risk_percentage": 0.0,
            "avg_work_hours": 0.0,
            "avg_sleep_hours": 0.0,
            "risk_distribution": {
                "labels": ["Low Risk (Rendah)", "Moderate Risk (Sedang)", "High Risk (Tinggi)"],
                "data": [0, 0, 0],
                "percentages": [0.0, 0.0, 0.0]
            },
            "work_sleep_by_risk": {
                "labels": ["Low Risk", "Moderate Risk", "High Risk"],
                "work_hours": [0.0, 0.0, 0.0],
                "sleep_hours": [0.0, 0.0, 0.0]
            },
            "mental_health_distribution": {
                "labels": ["Healthy (Prima)", "Needs Attention (Perlu Perhatian)", "Critical (Kritis)"],
                "data": [0, 0, 0]
            },
            "wellness_pillars": {
                "job_satisfaction": 0.0,
                "work_life_balance": 0.0,
                "productivity_score": 0.0,
                "life_satisfaction": 0.0
            },
            "top_occupations": []
        }

