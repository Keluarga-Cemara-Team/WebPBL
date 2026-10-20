import json
import logging
import urllib.request
import urllib.error
from typing import Dict, Any
from app.core.interfaces.ml_service import IMLPredictorService

logger = logging.getLogger(__name__)

class HttpMLPredictorService(IMLPredictorService):
    """
    Adapter External Service: Mengimplementasikan IMLPredictorService
    dengan memanggil REST API MachineLearningPBL melalui protokol HTTP.
    Menggunakan standard library (urllib) agar tidak mewajibkan dependensi pihak ketiga.
    """

    def __init__(self, ml_api_url: str):
        self.ml_api_url = ml_api_url

    def predict_burnout(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Kirim data fitur ke backend MachineLearningPBL.
        Jika server ML belum running, sediakan respons simulasi fallback.
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
            logger.info(f"Koneksi ke MachineLearningPBL ({self.ml_api_url}) belum aktif ({err}). Menggunakan kalkulasi heuristik.")

        return self._fallback_prediction(features)

    @staticmethod
    def _fallback_prediction(features: Dict[str, Any]) -> Dict[str, Any]:
        work_hours = float(features.get("work_hours", 8))
        sleep_hours = float(features.get("sleep_hours", 7))
        stress_level = int(features.get("stress_level", 3))

        score = (work_hours / 12 * 35) + ((10 - sleep_hours) / 10 * 30) + (stress_level / 5 * 35)
        score = min(max(round(score, 1), 5.0), 98.0)

        if score < 40:
            level = "Rendah (Low Risk)"
            badge_class = "success"
            desc = "Kondisi Anda berada dalam batas normal. Pertahankan pola istirahat yang baik."
        elif score < 70:
            level = "Sedang (Moderate Risk)"
            badge_class = "warning"
            desc = "Mulai terindikasi kelelahan kerja. Disarankan untuk mengambil jeda dan mengatur beban tugas."
        else:
            level = "Tinggi (High Risk / Burnout)"
            badge_class = "danger"
            desc = "Tingkat stres dan beban kerja tinggi terdeteksi. Segera lakukan pemulihan dan konsultasi."

        return {
            "is_simulation": True,
            "burnout_score": score,
            "burnout_level": level,
            "badge_class": badge_class,
            "recommendation": desc
        }
