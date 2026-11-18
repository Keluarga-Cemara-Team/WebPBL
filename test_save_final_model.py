import json
import tempfile
import unittest
from pathlib import Path

import joblib
import pandas as pd

from app import create_app
from app.core.use_cases.save_final_model import GetFinalModelUseCase, SaveFinalModelUseCase


class SaveFinalModelUseCaseTests(unittest.TestCase):
    def setUp(self):
        self.headers = ["Work_Hours", "Sleep_Quality", "Burnout_Score", "Burnout_Risk"]
        self.rows = []
        for label, base_hours in (("Low", 30), ("Moderate", 42), ("High", 58)):
            for index in range(10):
                self.rows.append(
                    [
                        str(base_hours + index),
                        ("Good", "Average", "Poor")[("Low", "Moderate", "High").index(label)],
                        "50",
                        label,
                    ]
                )

    def test_saves_pipeline_and_metadata_and_loaded_pipeline_predicts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline_path = Path(tmpdir) / "pipeline.joblib"
            metadata_path = Path(tmpdir) / "metadata.json"

            get_uc = GetFinalModelUseCase(pipeline_path, metadata_path)
            self.assertFalse(get_uc.execute()["is_saved"])

            save_uc = SaveFinalModelUseCase(pipeline_path, metadata_path)
            result = save_uc.execute(
                {
                    "dataset_name": "burnout_sample.csv",
                    "headers": self.headers,
                    "rows": self.rows,
                    "feature_columns": ["Work_Hours", "Sleep_Quality"],
                    "selected_model_name": "Random Forest GINI",
                    "preprocessing": {
                        "numeric_imputation": "mean",
                        "categorical_imputation": "mode",
                        "outlier_handling": "iqr_cap",
                        "encoding": "onehot",
                        "scaling": "standard",
                    },
                }
            )

            self.assertTrue(result["is_saved"])
            self.assertTrue(pipeline_path.exists())
            self.assertTrue(metadata_path.exists())

            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            self.assertEqual(metadata["model_name"], "Random Forest GINI")
            self.assertEqual(metadata["dataset_info"]["dataset_name"], "burnout_sample.csv")
            self.assertTrue(metadata["dataset_info"]["dataset_version"].startswith("v-"))
            self.assertEqual(metadata["feature_columns"], ["Work_Hours", "Sleep_Quality"])
            self.assertEqual(metadata["preprocessing"]["outlier_handling"], "iqr_cap")
            self.assertIn("final_test_metrics", metadata["evaluation_results"])

            loaded_pipeline = joblib.load(pipeline_path)
            predictions = loaded_pipeline.predict(
                pd.DataFrame({"Work_Hours": [31.0, 62.0], "Sleep_Quality": ["Good", "Poor"]})
            )
            self.assertTrue(set(predictions).issubset({"Low", "Moderate", "High"}))

            status_after = get_uc.execute()
            self.assertTrue(status_after["is_saved"])
            self.assertEqual(status_after["metadata"]["model_name"], "Random Forest GINI")

    def test_rejects_unknown_model_name_and_leakage_columns(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            save_uc = SaveFinalModelUseCase(
                Path(tmpdir) / "pipeline.joblib",
                Path(tmpdir) / "metadata.json",
            )

            with self.assertRaisesRegex(ValueError, "tidak dikenali"):
                save_uc.execute(
                    {
                        "headers": self.headers,
                        "rows": self.rows,
                        "feature_columns": ["Work_Hours", "Sleep_Quality"],
                        "selected_model_name": "Unknown Model",
                    }
                )

            with self.assertRaisesRegex(ValueError, "data leakage"):
                save_uc.execute(
                    {
                        "headers": self.headers,
                        "rows": self.rows,
                        "feature_columns": ["Work_Hours", "Burnout_Score"],
                        "selected_model_name": "Gaussian Naive Bayes",
                    }
                )

    def test_flask_endpoints_finalize_and_get_final_model(self):
        app = create_app("development")
        app.config["TESTING"] = True
        with tempfile.TemporaryDirectory() as tmpdir:
            app.config["FINAL_MODEL_PIPELINE_PATH"] = Path(tmpdir) / "pipeline.joblib"
            app.config["FINAL_MODEL_METADATA_PATH"] = Path(tmpdir) / "metadata.json"

            client = app.test_client()
            with client.session_transaction() as sess:
                sess["logged_in"] = True
                sess["username"] = "admin"

            get_before = client.get("/dataset-management/final-model")
            self.assertEqual(get_before.status_code, 200)
            self.assertFalse(get_before.get_json()["data"]["is_saved"])

            post_res = client.post(
                "/dataset-management/finalize",
                json={
                    "dataset_name": "test_web.csv",
                    "headers": self.headers,
                    "rows": self.rows,
                    "feature_columns": ["Work_Hours", "Sleep_Quality"],
                    "selected_model_name": "Gaussian Naive Bayes",
                },
            )
            self.assertEqual(post_res.status_code, 200)
            post_json = post_res.get_json()
            self.assertEqual(post_json["status"], "success")
            self.assertEqual(post_json["data"]["metadata"]["model_name"], "Gaussian Naive Bayes")

            get_after = client.get("/dataset-management/final-model")
            self.assertEqual(get_after.status_code, 200)
            self.assertTrue(get_after.get_json()["data"]["is_saved"])


if __name__ == "__main__":
    unittest.main()
