from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import joblib
import pandas as pd
from sklearn.base import clone

from app.core.use_cases.compare_dataset_models import CompareDatasetModelsUseCase


class SaveFinalModelUseCase:
    """Train the selected candidate pipeline and persist both pipeline (.joblib) and metadata (.json)."""

    def __init__(self, pipeline_path: Path, metadata_path: Path):
        self.pipeline_path = Path(pipeline_path)
        self.metadata_path = Path(metadata_path)

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        selected_model_name = payload.get("selected_model_name")
        if not isinstance(selected_model_name, str) or not selected_model_name.strip():
            raise ValueError("Nama model final yang dipilih harus diisi.")
        selected_model_name = selected_model_name.strip()

        candidates_map = dict(CompareDatasetModelsUseCase.get_candidates())
        if selected_model_name not in candidates_map:
            raise ValueError(
                f"Model '{selected_model_name}' tidak dikenali. Pilihan valid: {', '.join(candidates_map.keys())}."
            )

        comparer = CompareDatasetModelsUseCase()
        prepared = comparer.prepare_and_split(payload)

        x_train = prepared["x_train"]
        y_train = prepared["y_train"]
        x_validation = prepared["x_validation"]
        y_validation = prepared["y_validation"]
        x_test = prepared["x_test"]
        y_test = prepared["y_test"]
        numeric_columns = prepared["numeric_columns"]
        categorical_columns = prepared["categorical_columns"]
        active_features = prepared["active_features"]
        preprocessing = prepared["preprocessing"]
        validation_method = prepared["validation_method"]
        validation_folds = prepared["validation_folds"]
        train_percent = prepared["train_percent"]
        validation_percent = prepared["validation_percent"]
        test_percent = prepared["test_percent"]
        target_column = prepared["target_column"]
        excluded_leakage_columns = prepared["excluded_leakage_columns"]
        frame = prepared["frame"]
        class_counts = prepared["class_counts"]
        rows_received = prepared["rows_received"]

        if validation_method == "cross_validation":
            final_x_train, final_y_train = x_train, y_train
        else:
            final_x_train = pd.concat([x_train, x_validation])
            final_y_train = pd.concat([y_train, y_validation])

        final_x_train, final_y_train, dropped_outliers = comparer._drop_training_outliers(
            final_x_train,
            final_y_train,
            numeric_columns if preprocessing["outlier_handling"] == "drop" else [],
        )
        comparer._ensure_training_classes(final_y_train, "data latih akhir")

        selected_pipeline = comparer._build_model_pipeline(
            numeric_columns,
            categorical_columns,
            clone(candidates_map[selected_model_name]),
            preprocessing,
        )
        comparer._set_knn_neighbors(selected_pipeline, len(final_y_train))
        selected_pipeline.fit(final_x_train, final_y_train)

        test_predictions = selected_pipeline.predict(x_test)
        raw_test_metrics = comparer._calculate_metrics(y_test, test_predictions)
        test_prediction_summary = comparer._summarize_predictions(
            y_test,
            [str(val) for val in test_predictions.tolist()],
            x_test.index.tolist(),
        )
        final_test_metrics = {
            "accuracy": round(raw_test_metrics["accuracy"], 4),
            "precision_macro": round(raw_test_metrics["precision_macro"], 4),
            "recall_macro": round(raw_test_metrics["recall_macro"], 4),
            "f1_macro": round(raw_test_metrics["f1_macro"], 4),
            "raw_metrics": raw_test_metrics,
            "confusion_matrix": test_prediction_summary["confusion_matrix"],
            "prediction_distribution": test_prediction_summary["prediction_distribution"],
            "sample_predictions": test_prediction_summary["sample_predictions"],
        }

        dataset_name = str(payload.get("dataset_name") or "dataset.csv").strip() or "dataset.csv"
        dataset_fingerprint_src = json.dumps(
            {
                "dataset_name": dataset_name,
                "rows_received": rows_received,
                "rows_used": len(frame),
                "feature_columns": active_features,
                "class_distribution": {
                    label: int(class_counts[label]) for label in comparer.LABELS
                },
            },
            sort_keys=True,
        )
        dataset_hash = hashlib.sha256(dataset_fingerprint_src.encode("utf-8")).hexdigest()[:12]
        saved_at = datetime.now().astimezone().isoformat(timespec="seconds")

        validation_summary = payload.get("validation_summary")
        if not isinstance(validation_summary, dict):
            validation_summary = None

        metadata: Dict[str, Any] = {
            "model_name": selected_model_name,
            "saved_at": saved_at,
            "dataset_info": {
                "dataset_name": dataset_name,
                "dataset_version": f"v-{dataset_hash}",
                "rows_received": rows_received,
                "rows_used": len(frame),
                "train_rows": len(x_train),
                "validation_rows": len(x_validation),
                "test_rows": len(x_test),
                "final_training_outliers_removed": dropped_outliers,
                "target_column": target_column,
                "labels": list(comparer.LABELS),
                "class_distribution": {
                    label: int(class_counts[label]) for label in comparer.LABELS
                },
            },
            "feature_columns": active_features,
            "numeric_columns": numeric_columns,
            "categorical_columns": categorical_columns,
            "leakage_check": {
                "passed": True,
                "excluded_leakage_columns": excluded_leakage_columns,
            },
            "preprocessing": preprocessing,
            "split_config": {
                "validation_method": validation_method,
                "validation_folds": validation_folds,
                "train_percent": train_percent,
                "validation_percent": validation_percent,
                "test_percent": test_percent,
                "deduplicate": bool(payload.get("deduplicate", True)),
                "sample_size_applied": prepared.get("sample_size_applied"),
                "random_state": comparer.RANDOM_STATE,
            },
            "evaluation_results": {
                "validation_summary": validation_summary,
                "final_test_metrics": final_test_metrics,
            },
            "artifacts": {
                "pipeline_path": str(self.pipeline_path),
                "metadata_path": str(self.metadata_path),
            },
        }

        self.pipeline_path.parent.mkdir(parents=True, exist_ok=True)
        self.metadata_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(selected_pipeline, self.pipeline_path)
        self.metadata_path.write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        return {
            "is_saved": True,
            "metadata": metadata,
            "pipeline_path": str(self.pipeline_path),
            "metadata_path": str(self.metadata_path),
        }


class GetFinalModelUseCase:
    """Read persisted final model metadata and verify its pipeline artifact exists."""

    def __init__(self, pipeline_path: Path, metadata_path: Path):
        self.pipeline_path = Path(pipeline_path)
        self.metadata_path = Path(metadata_path)

    def execute(self) -> Dict[str, Any]:
        if not self.pipeline_path.exists() or not self.metadata_path.exists():
            return {
                "is_saved": False,
                "metadata": None,
                "pipeline_path": str(self.pipeline_path),
                "metadata_path": str(self.metadata_path),
            }

        try:
            metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {
                "is_saved": False,
                "metadata": None,
                "pipeline_path": str(self.pipeline_path),
                "metadata_path": str(self.metadata_path),
            }

        return {
            "is_saved": True,
            "metadata": metadata,
            "pipeline_path": str(self.pipeline_path),
            "metadata_path": str(self.metadata_path),
        }
