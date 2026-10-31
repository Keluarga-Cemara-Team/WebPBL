import json
import logging
import urllib.request
import urllib.error
from typing import Dict, Any
from app.core.interfaces.ml_service import IMLPredictorService

logger = logging.getLogger(__name__)

class HttpMLPredictorService(IMLPredictorService):
    """
    Adapter External Service: Menghubungkan WebPBL ke MachineLearningPBL API
    menggunakan 40 atribut fitur standar dari mental_health_burnout_prediction_dataset.csv.
    Dilengkapi fallback heuristik jika server ML offline.
    """

    def __init__(self, ml_api_url: str):
        self.ml_api_url = ml_api_url

    def predict_burnout(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Kirim data fitur lengkap ke backend MachineLearningPBL.
        """
        try:
            req_data = json.dumps(features).encode("utf-8")
            req = urllib.request.Request(
                self.ml_api_url,
                data=req_data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=3.0) as response:
                if response.status == 200:
                    resp_body = response.read().decode("utf-8")
                    result = json.loads(resp_body)
                    result["is_simulation"] = False
                    return result
        except Exception as err:
            logger.info(f"Koneksi ke MachineLearningPBL ({self.ml_api_url}) belum aktif ({err}). Menggunakan model estimasi dataset.")

        return self._fallback_prediction(features)

    @staticmethod
    def _fallback_prediction(f: Dict[str, Any]) -> Dict[str, Any]:
        """
        Kalkulasi estimasi burnout berbasis korelasi atribut dari dataset mental_health_burnout_prediction_dataset.csv
        """
        work_hours = float(f.get("work_hours_per_week", 40.0))
        sleep_hours = float(f.get("sleep_hours", 7.0))
        anxiety = float(f.get("anxiety_score", 30.0))
        depression = float(f.get("depression_score", 25.0))
        job_satisfaction = float(f.get("job_satisfaction", 6.0))
        work_life_balance = float(f.get("work_life_balance", 5.0))
        stress_level = str(f.get("stress_level", "Moderate")).lower()
        chronic_stress = str(f.get("chronic_stress", "No")).lower() == "yes"

        # Bobot stres dasar
        stress_weight = 30.0 if stress_level == "high" else (18.0 if stress_level == "moderate" else 8.0)
        if chronic_stress:
            stress_weight += 12.0

        # Formula skor komprehensif
        score = (
            stress_weight +
            (max(work_hours - 35, 0) / 45 * 25.0) +
            (max(8.0 - sleep_hours, 0) / 5 * 18.0) +
            ((anxiety + depression) / 200 * 25.0) -
            ((job_satisfaction + work_life_balance) / 20 * 15.0)
        )
        score = round(min(max(score, 5.0), 98.0), 1)

        # Klasifikasi target sesuai dataset
        if score < 40.0:
            risk = "Low"
            status = "Healthy"
            badge_class = "success"
            rec = "Maintain Healthy Routine"
        elif score < 68.0:
            risk = "Moderate"
            status = "Needs Attention"
            badge_class = "warning"
            if work_hours > 50:
                rec = "Reduce Workload"
            elif sleep_hours < 6.0:
                rec = "Take Regular Breaks"
            else:
                rec = "Practice Mindfulness"
        else:
            risk = "High"
            status = "Critical"
            badge_class = "danger"
            if anxiety > 60 or depression > 60 or chronic_stress:
                rec = "Seek Professional Support"
            else:
                rec = "Reduce Workload"

        return {
            "is_simulation": True,
            "burnout_score": score,
            "burnout_risk": risk,
            "mental_health_status": status,
            "ai_wellness_recommendation": rec,
            "badge_class": badge_class,
            "burnout_level": f"{risk} Risk"
        }
