import json
import logging
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import joblib
import pandas as pd

from app.core.interfaces.ml_service import IMLPredictorService

logger = logging.getLogger(__name__)


class HttpMLPredictorService(IMLPredictorService):
    """
    Adapter External Service:
    1. Prioritas utama: menggunakan pipeline model final tersimpan (data/final_model/pipeline.joblib)
       jika sudah ditetapkan di halaman Dataset Management.
    2. Fallback 1: memanggil MachineLearningPBL HTTP API (port 8000).
    3. Fallback 2: estimasi heuristik dataset jika kedua layanan belum tersedia.
    """

    def __init__(
        self,
        ml_api_url: str,
        pipeline_path: Optional[Path] = None,
        metadata_path: Optional[Path] = None,
    ):
        self.ml_api_url = ml_api_url
        self.pipeline_path = Path(pipeline_path) if pipeline_path else None
        self.metadata_path = Path(metadata_path) if metadata_path else None
        self._cached_mtime: Optional[Tuple[float, float]] = None
        self._cached_pipeline: Any = None
        self._cached_metadata: Optional[Dict[str, Any]] = None

    @staticmethod
    def _normalize_key(value: Any) -> str:
        return "".join(ch.lower() for ch in str(value) if ch.isalnum())

    def _load_final_model(self) -> Optional[Tuple[Any, Dict[str, Any]]]:
        if not self.pipeline_path or not self.metadata_path:
            return None
        if not self.pipeline_path.exists() or not self.metadata_path.exists():
            self._cached_mtime = None
            self._cached_pipeline = None
            self._cached_metadata = None
            return None

        current_mtime = (
            self.pipeline_path.stat().st_mtime,
            self.metadata_path.stat().st_mtime,
        )
        if (
            self._cached_mtime == current_mtime
            and self._cached_pipeline is not None
            and self._cached_metadata is not None
        ):
            return self._cached_pipeline, self._cached_metadata

        pipeline = joblib.load(self.pipeline_path)
        metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        self._cached_mtime = current_mtime
        self._cached_pipeline = pipeline
        self._cached_metadata = metadata
        return pipeline, metadata

    @classmethod
    def _build_pipeline_input_frame(
        cls,
        features: Dict[str, Any],
        metadata: Dict[str, Any],
    ) -> pd.DataFrame:
        feature_columns = metadata.get("feature_columns") or []
        numeric_set = {cls._normalize_key(col) for col in (metadata.get("numeric_columns") or [])}
        normalized_features = {
            cls._normalize_key(key): val for key, val in (features or {}).items()
        }

        row_data: Dict[str, Any] = {}
        for col in feature_columns:
            norm_col = cls._normalize_key(col)
            raw_val = normalized_features.get(norm_col)
            if isinstance(raw_val, str):
                raw_val = raw_val.strip()
                if raw_val == "" or raw_val.lower() in {"nan", "null", "none"}:
                    raw_val = None

            if norm_col in numeric_set:
                if raw_val is None:
                    row_data[col] = None
                else:
                    try:
                        row_data[col] = float(raw_val)
                    except (ValueError, TypeError):
                        row_data[col] = None
            else:
                row_data[col] = str(raw_val) if raw_val is not None else None

        return pd.DataFrame([row_data], columns=feature_columns)

    @staticmethod
    def _build_recommendation_and_status(
        predicted_risk: str,
        features: Dict[str, Any],
    ) -> Tuple[str, str, str]:
        def _to_float(key: str, default: float) -> float:
            try:
                val = features.get(key)
                return float(val) if val is not None and str(val).strip() != "" else default
            except (ValueError, TypeError):
                return default

        work_hours = _to_float("work_hours_per_week", 40.0)
        sleep_hours = _to_float("sleep_hours", 7.0)
        anxiety = _to_float("anxiety_score", 30.0)
        depression = _to_float("depression_score", 25.0)
        chronic_stress = str(features.get("chronic_stress", "No")).lower() == "yes"

        risk_lower = predicted_risk.lower()
        if risk_lower == "low":
            return "Healthy", "success", "Maintain Healthy Routine"
        if risk_lower == "moderate":
            if work_hours > 50:
                rec = "Reduce Workload"
            elif sleep_hours < 6.0:
                rec = "Take Regular Breaks"
            else:
                rec = "Practice Mindfulness"
            return "Needs Attention", "warning", rec

        rec = (
            "Seek Professional Support"
            if (anxiety > 60 or depression > 60 or chronic_stress)
            else "Reduce Workload"
        )
        return "Critical", "danger", rec

    def _predict_with_final_pipeline(
        self,
        features: Dict[str, Any],
        pipeline: Any,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        input_df = self._build_pipeline_input_frame(features, metadata)
        predicted_risk = str(pipeline.predict(input_df)[0])

        score_map = {"Low": 20.0, "Moderate": 55.0, "High": 88.0}
        if hasattr(pipeline, "predict_proba"):
            try:
                probs = pipeline.predict_proba(input_df)[0]
                classes = [str(c) for c in pipeline.classes_]
                weighted = sum(
                    float(prob) * score_map.get(cls_name, 55.0)
                    for cls_name, prob in zip(classes, probs)
                )
                score = round(min(max(weighted, 5.0), 98.0), 1)
            except Exception:
                score = score_map.get(predicted_risk, 55.0)
        else:
            score = score_map.get(predicted_risk, 55.0)

        status, badge_class, rec = self._build_recommendation_and_status(
            predicted_risk, features
        )

        return {
            "is_simulation": False,
            "prediction_source": "final_model_pipeline",
            "model_name": metadata.get("model_name"),
            "dataset_version": metadata.get("dataset_info", {}).get("dataset_version"),
            "burnout_score": score,
            "burnout_risk": predicted_risk,
            "mental_health_status": status,
            "ai_wellness_recommendation": rec,
            "badge_class": badge_class,
            "burnout_level": f"{predicted_risk} Risk",
        }

    def predict_burnout(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gunakan pipeline model final tersimpan bila ada; jika belum ada, fallback ke API HTTP atau estimasi.
        """
        try:
            loaded = self._load_final_model()
            if loaded is not None:
                pipeline, metadata = loaded
                return self._predict_with_final_pipeline(features, pipeline, metadata)
        except Exception as err:
            logger.warning(f"Gagal memprediksi menggunakan pipeline model final: {err}")

        try:
            req_data = json.dumps(features).encode("utf-8")
            req = urllib.request.Request(
                self.ml_api_url,
                data=req_data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=3.0) as response:
                if response.status == 200:
                    resp_body = response.read().decode("utf-8")
                    result = json.loads(resp_body)
                    result["is_simulation"] = False
                    result.setdefault("prediction_source", "external_http_api")
                    return result
        except Exception as err:
            logger.info(
                f"Koneksi ke MachineLearningPBL ({self.ml_api_url}) belum aktif ({err}). Menggunakan model estimasi dataset."
            )

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

        stress_weight = 30.0 if stress_level == "high" else (18.0 if stress_level == "moderate" else 8.0)
        if chronic_stress:
            stress_weight += 12.0

        score = (
            stress_weight
            + (max(work_hours - 35, 0) / 45 * 25.0)
            + (max(8.0 - sleep_hours, 0) / 5 * 18.0)
            + ((anxiety + depression) / 200 * 25.0)
            - ((job_satisfaction + work_life_balance) / 20 * 15.0)
        )
        score = round(min(max(score, 5.0), 98.0), 1)

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
            "prediction_source": "heuristic_fallback",
            "burnout_score": score,
            "burnout_risk": risk,
            "mental_health_status": status,
            "ai_wellness_recommendation": rec,
            "badge_class": badge_class,
            "burnout_level": f"{risk} Risk",
        }
