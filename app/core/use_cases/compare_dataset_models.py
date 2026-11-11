from __future__ import annotations

import random
from time import perf_counter
from typing import Any, Dict, List, Optional, Sequence

import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin, clone
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import StratifiedKFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder, OrdinalEncoder, StandardScaler
from sklearn.svm import SVC


class _IQRCapper(BaseEstimator, TransformerMixin):
    def __init__(self, numeric_columns: Sequence[str]):
        self.numeric_columns = numeric_columns

    def fit(self, x: pd.DataFrame, y: Any = None) -> "_IQRCapper":
        self.bounds_: Dict[str, tuple[float, float]] = {}
        for column in self.numeric_columns:
            values = pd.to_numeric(x[column], errors="coerce").dropna()
            if values.empty:
                continue
            q1 = float(values.quantile(0.25))
            q3 = float(values.quantile(0.75))
            spread = q3 - q1
            self.bounds_[column] = (q1 - 1.5 * spread, q3 + 1.5 * spread)
        return self

    def transform(self, x: pd.DataFrame) -> pd.DataFrame:
        transformed = x.copy()
        for column, (lower, upper) in self.bounds_.items():
            transformed[column] = pd.to_numeric(
                transformed[column], errors="coerce"
            ).clip(lower=lower, upper=upper)
        return transformed


class CompareDatasetModelsUseCase:
    """Train and evaluate candidate classifiers without persisting any model."""

    LABELS = ("Low", "Moderate", "High")
    MAX_ROWS = 25_000
    RANDOM_STATE = 42

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        headers = payload.get("headers")
        rows = payload.get("rows")
        feature_columns = payload.get("feature_columns")
        deduplicate = payload.get("deduplicate", True)
        train_percent = payload.get("train_percent", 70)
        validation_percent = payload.get("validation_percent", 15)
        test_percent = payload.get("test_percent", 15)
        validation_method = payload.get("validation_method", "holdout")
        preprocessing = payload.get("preprocessing", {})

        if not isinstance(headers, list) or not headers or not all(
            isinstance(header, str) and header.strip() for header in headers
        ):
            raise ValueError("Header dataset tidak valid.")
        if not isinstance(rows, list) or not rows:
            raise ValueError("Dataset tidak memiliki baris data.")
        if len(rows) > self.MAX_ROWS:
            raise ValueError(f"Dataset melebihi batas {self.MAX_ROWS:,} baris.")
        if not isinstance(feature_columns, list) or not all(
            isinstance(column, str) for column in feature_columns
        ):
            raise ValueError("Daftar fitur tidak valid.")
        if not isinstance(deduplicate, bool):
            raise ValueError("Opsi penghapusan duplikat harus berupa boolean.")
        if not isinstance(validation_method, str) or validation_method not in {
            "holdout",
            "cross_validation",
        }:
            raise ValueError("Metode validasi tidak dikenali.")
        if not isinstance(preprocessing, dict):
            raise ValueError("Pengaturan preprocessing harus berupa object.")
        preprocessing_defaults = {
            "numeric_imputation": "mean",
            "categorical_imputation": "mode",
            "outlier_handling": "none",
            "encoding": "onehot",
            "scaling": "standard",
        }
        preprocessing = {
            **preprocessing_defaults,
            **preprocessing,
        }
        allowed_preprocessing = {
            "numeric_imputation": {"mean", "median", "mode", "zero", "drop"},
            "categorical_imputation": {"mode", "unknown", "drop"},
            "outlier_handling": {"none", "iqr_cap", "drop"},
            "encoding": {"label", "onehot", "none"},
            "scaling": {"none", "minmax", "standard"},
        }
        for setting, allowed_values in allowed_preprocessing.items():
            if preprocessing[setting] not in allowed_values:
                raise ValueError(f"Pengaturan preprocessing {setting} tidak valid.")
        percentages = (train_percent, validation_percent, test_percent)
        if any(
            isinstance(value, bool) or not isinstance(value, int)
            for value in percentages
        ):
            raise ValueError("Persentase data latih, validasi, dan uji harus berupa bilangan bulat.")
        valid_holdout_split = (
            train_percent >= 50
            and train_percent <= 90
            and validation_percent >= 5
            and validation_percent <= 45
            and test_percent >= 5
            and test_percent <= 45
            and sum(percentages) == 100
        )
        valid_cross_validation_split = (
            train_percent >= 50
            and train_percent <= 95
            and validation_percent == 0
            and test_percent >= 5
            and test_percent <= 50
            and train_percent + test_percent == 100
        )
        if not (
            valid_holdout_split
            if validation_method == "holdout"
            else valid_cross_validation_split
        ):
            raise ValueError(
                "Pembagian holdout memerlukan data latih 50–90%, validasi dan uji masing-masing 5–45%, "
                "dengan total 100%. Pembagian cross-validation memerlukan data latih 50–95%, "
                "data validasi 0%, data uji 5–50%, serta total latih dan uji 100%."
            )
        if any(not isinstance(row, list) or len(row) != len(headers) for row in rows):
            raise ValueError("Jumlah nilai pada baris tidak sesuai dengan jumlah kolom.")

        cleaned_headers = [header.strip() for header in headers]
        normalized_headers = [self._normalize_header(header) for header in cleaned_headers]
        if len(set(normalized_headers)) != len(normalized_headers):
            raise ValueError("Nama kolom harus unik.")

        target_column = self._find_target_column(cleaned_headers)
        if target_column is None:
            raise ValueError("Kolom target Burnout_Risk atau Burnout_Level tidak ditemukan.")
        if not feature_columns:
            raise ValueError("Pilih setidaknya satu kolom fitur selain kolom target.")

        feature_columns = list(dict.fromkeys(column.strip() for column in feature_columns))
        unknown_columns = [column for column in feature_columns if column not in cleaned_headers]
        if unknown_columns:
            raise ValueError(f"Kolom fitur tidak ditemukan: {', '.join(unknown_columns)}.")
        if any(self._is_target_column(column) for column in feature_columns):
            raise ValueError("Kolom target tidak boleh digunakan sebagai fitur.")

        frame = pd.DataFrame(rows, columns=cleaned_headers)
        labels = frame[target_column].map(self._normalize_label)
        valid_label_mask = labels.notna()
        invalid_label_count = int((~valid_label_mask).sum())
        frame = frame.loc[valid_label_mask, feature_columns].copy()
        labels = labels.loc[valid_label_mask]

        if frame.empty:
            raise ValueError("Tidak ada baris dengan label Low, Moderate, atau High yang valid.")

        for column in feature_columns:
            frame[column] = frame[column].map(self._clean_value)

        preprocessing_excluded_rows = 0
        drop_missing_columns = []
        for column in feature_columns:
            non_empty_values = frame[column].dropna()
            numeric_feature = (
                not non_empty_values.empty
                and pd.to_numeric(non_empty_values, errors="coerce").notna().all()
            )
            imputation_setting = preprocessing[
                "numeric_imputation" if numeric_feature else "categorical_imputation"
            ]
            if imputation_setting == "drop":
                drop_missing_columns.append(column)
        if drop_missing_columns:
            missing_rows = frame[drop_missing_columns].isna().any(axis=1)
            preprocessing_excluded_rows += int(missing_rows.sum())
            frame = frame.loc[~missing_rows].copy()
            labels = labels.loc[~missing_rows]
            if frame.empty:
                raise ValueError(
                    "Tidak ada baris tersisa setelah baris dengan nilai fitur kosong dihapus."
                )

        deduplication_frame = frame.copy()
        target_marker = "__training_target__"
        while target_marker in deduplication_frame.columns:
            target_marker += "_"
        deduplication_frame[target_marker] = labels
        duplicate_mask = deduplication_frame.duplicated(keep="first")
        duplicate_count = int(duplicate_mask.sum()) if deduplicate else 0
        if deduplicate:
            frame = frame.loc[~duplicate_mask].copy()
            labels = labels.loc[~duplicate_mask]

        missing_classes = [label for label in self.LABELS if label not in set(labels)]
        if missing_classes:
            raise ValueError(
                "Dataset harus memiliki label Low, Moderate, dan High. "
                f"Label yang tidak tersedia: {', '.join(missing_classes)}."
            )

        class_counts = labels.value_counts().reindex(self.LABELS, fill_value=0)
        minimum_class_rows = 3 if validation_method == "holdout" else 4
        if any(int(count) < minimum_class_rows for count in class_counts):
            counts_summary = ", ".join(
                f"{label}: {int(class_counts[label])}" for label in self.LABELS
            )
            duplicate_note = (
                f" {duplicate_count} baris duplikat dihapus berdasarkan fitur terpilih dan label."
                if deduplicate and duplicate_count
                else ""
            )
            raise ValueError(
                "Data belum cukup untuk pembagian stratified. "
                f"Jumlah setelah pembersihan — {counts_summary}. "
                f"Minimal {minimum_class_rows} baris berlabel valid per kelas diperlukan "
                f"untuk metode {validation_method.replace('_', ' ')}.{duplicate_note} "
                "Periksa kembali fitur yang dipilih dan label pada dataset."
            )
        if len(frame) < 15:
            raise ValueError("Dataset harus memiliki minimal 15 baris berlabel valid setelah dibersihkan.")

        numeric_columns: List[str] = []
        categorical_columns: List[str] = []
        for column in feature_columns:
            non_empty = frame[column].notna()
            if not non_empty.any():
                continue
            numeric_values = pd.to_numeric(frame[column], errors="coerce")
            if numeric_values.loc[non_empty].notna().all():
                numeric_columns.append(column)
                frame[column] = numeric_values
            else:
                categorical_columns.append(column)
                frame[column] = frame[column].map(
                    lambda value: str(value).strip() if pd.notna(value) else None
                )

        active_features = numeric_columns + categorical_columns
        if not active_features:
            raise ValueError("Tidak ada fitur berisi nilai yang dapat digunakan.")
        if categorical_columns and preprocessing["encoding"] == "none":
            raise ValueError(
                "Fitur kategorikal tidak dapat dipakai model tanpa encoding. "
                "Pilih Label Encoding atau One-Hot Encoding."
            )
        frame = frame[active_features]

        if validation_method == "cross_validation":
            train_indices, test_indices = self._stratified_train_test_indices(
                labels, train_percent, minimum_train_rows=3
            )
            x_train, x_test = frame.loc[train_indices], frame.loc[test_indices]
            y_train, y_test = labels.loc[train_indices], labels.loc[test_indices]
            x_validation = frame.iloc[0:0]
            y_validation = labels.iloc[0:0]
            validation_folds = min(
                5,
                int(y_train.value_counts().reindex(self.LABELS).min()),
            )
        else:
            split_indices = self._stratified_split_indices(
                labels,
                (train_percent, validation_percent, test_percent),
            )
            x_train, x_validation, x_test = (
                frame.loc[indices] for indices in split_indices
            )
            y_train, y_validation, y_test = (
                labels.loc[indices] for indices in split_indices
            )
            validation_folds = None

            for split_name, split_labels in (
                ("latih", y_train),
                ("validasi", y_validation),
                ("uji", y_test),
            ):
                missing_split_classes = [
                    label for label in self.LABELS if label not in set(split_labels)
                ]
                if missing_split_classes:
                    raise ValueError(
                        f"Bagian data {split_name} tidak memuat kelas "
                        f"{', '.join(missing_split_classes)}. Tambahkan data atau ubah persentase pembagian."
                    )

        candidates = [
            ("Gaussian Naive Bayes", GaussianNB()),
            (
                "SVM RBF",
                SVC(kernel="rbf", C=1.0, gamma="scale"),
            ),
            (
                "Logistic Regression L1",
                LogisticRegression(
                    solver="saga",
                    l1_ratio=1.0,
                    C=0.01,
                    max_iter=5000,
                    random_state=self.RANDOM_STATE,
                ),
            ),
            (
                "KNN Manhattan",
                KNeighborsClassifier(
                    n_neighbors=5,
                    metric="manhattan",
                    weights="uniform",
                ),
            ),
            (
                "Random Forest GINI",
                RandomForestClassifier(
                    criterion="gini",
                    n_estimators=100,
                    random_state=self.RANDOM_STATE,
                    n_jobs=-1,
                ),
            ),
        ]

        results = []
        for model_name, classifier in candidates:
            started_at = perf_counter()
            if validation_method == "cross_validation":
                fold_results = []
                fit_time = 0.0
                splitter = StratifiedKFold(
                    n_splits=validation_folds,
                    shuffle=True,
                    random_state=self.RANDOM_STATE,
                )
                for fold_train_positions, fold_validation_positions in splitter.split(
                    x_train, y_train
                ):
                    fold_x_train = x_train.iloc[fold_train_positions]
                    fold_y_train = y_train.iloc[fold_train_positions]
                    fold_x_validation = x_train.iloc[fold_validation_positions]
                    fold_y_validation = y_train.iloc[fold_validation_positions]
                    fold_x_train, fold_y_train, dropped_outliers = (
                        self._drop_training_outliers(
                            fold_x_train, fold_y_train, numeric_columns
                            if preprocessing["outlier_handling"] == "drop"
                            else []
                        )
                    )
                    self._ensure_training_classes(fold_y_train, "fold latih")
                    fold_pipeline = self._build_model_pipeline(
                        numeric_columns,
                        categorical_columns,
                        classifier,
                        preprocessing,
                    )
                    self._set_knn_neighbors(fold_pipeline, len(fold_y_train))
                    fold_started_at = perf_counter()
                    fold_pipeline.fit(fold_x_train, fold_y_train)
                    fit_time += perf_counter() - fold_started_at
                    fold_predictions = fold_pipeline.predict(fold_x_validation)
                    fold_results.append(
                        self._calculate_metrics(fold_y_validation, fold_predictions)
                    )
                validation_metrics = {
                    metric: round(
                        sum(fold[metric] for fold in fold_results) / len(fold_results),
                        4,
                    )
                    for metric in ("accuracy", "precision_macro", "recall_macro", "f1_macro")
                }
                training_time = fit_time
            else:
                fit_x_train, fit_y_train, dropped_outliers = self._drop_training_outliers(
                    x_train,
                    y_train,
                    numeric_columns
                    if preprocessing["outlier_handling"] == "drop"
                    else [],
                )
                self._ensure_training_classes(fit_y_train, "data latih")
                pipeline = self._build_model_pipeline(
                    numeric_columns,
                    categorical_columns,
                    classifier,
                    preprocessing,
                )
                self._set_knn_neighbors(pipeline, len(fit_y_train))
                pipeline.fit(fit_x_train, fit_y_train)
                validation_predictions = pipeline.predict(x_validation)
                validation_metrics = self._calculate_metrics(
                    y_validation, validation_predictions
                )
                training_time = perf_counter() - started_at

            results.append(
                {
                    "model_name": model_name,
                    "validation_accuracy": validation_metrics["accuracy"],
                    "validation_precision_macro": validation_metrics["precision_macro"],
                    "validation_recall_macro": validation_metrics["recall_macro"],
                    "validation_f1_macro": validation_metrics["f1_macro"],
                    "training_time_seconds": round(float(training_time), 4),
                    "classifier": classifier,
                }
            )

        results.sort(
            key=lambda result: (
                result["validation_f1_macro"],
                result["validation_accuracy"],
                result["validation_precision_macro"],
            ),
            reverse=True,
        )
        selected_model = results[0]
        selected_classifier = selected_model["classifier"]
        if validation_method == "cross_validation":
            final_x_train, final_y_train = x_train, y_train
        else:
            final_x_train = pd.concat([x_train, x_validation])
            final_y_train = pd.concat([y_train, y_validation])
        final_x_train, final_y_train, dropped_outliers = self._drop_training_outliers(
            final_x_train,
            final_y_train,
            numeric_columns
            if preprocessing["outlier_handling"] == "drop"
            else [],
        )
        self._ensure_training_classes(final_y_train, "data latih akhir")
        selected_pipeline = self._build_model_pipeline(
            numeric_columns,
            categorical_columns,
            selected_classifier,
            preprocessing,
        )
        self._set_knn_neighbors(selected_pipeline, len(final_y_train))
        selected_pipeline.fit(final_x_train, final_y_train)
        test_predictions = selected_pipeline.predict(x_test)
        final_test_metrics = {
            "accuracy": round(float(accuracy_score(y_test, test_predictions)), 4),
            "precision_macro": round(
                float(precision_score(y_test, test_predictions, labels=self.LABELS, average="macro", zero_division=0)),
                4,
            ),
            "recall_macro": round(
                float(recall_score(y_test, test_predictions, labels=self.LABELS, average="macro", zero_division=0)),
                4,
            ),
            "f1_macro": round(
                float(f1_score(y_test, test_predictions, labels=self.LABELS, average="macro", zero_division=0)),
                4,
            ),
            "confusion_matrix": confusion_matrix(
                y_test, test_predictions, labels=self.LABELS
            ).tolist(),
        }
        for result in results:
            result.pop("classifier")

        return {
            "target_column": target_column,
            "labels": list(self.LABELS),
            "rows_received": len(rows),
            "invalid_label_rows_excluded": invalid_label_count,
            "duplicate_rows_removed": duplicate_count,
            "missing_feature_rows_removed": preprocessing_excluded_rows,
            "final_training_outliers_removed": dropped_outliers,
            "rows_used": len(frame),
            "train_rows": len(x_train),
            "validation_rows": len(x_validation),
            "test_rows": len(x_test),
            "split_percentages": {
                "train": train_percent,
                "validation": validation_percent,
                "test": test_percent,
            },
            "validation_method": validation_method,
            "validation_folds": validation_folds,
            "preprocessing": preprocessing,
            "actual_split_percentages": {
                "train": round(len(x_train) / len(frame) * 100, 1),
                "validation": round(len(x_validation) / len(frame) * 100, 1),
                "test": round(len(x_test) / len(frame) * 100, 1),
            },
            "feature_columns": active_features,
            "class_distribution": {
                label: int(class_counts[label]) for label in self.LABELS
            },
            "random_state": self.RANDOM_STATE,
            "results": results,
            "top_evaluated_model": selected_model["model_name"],
            "final_test_model": selected_model["model_name"],
            "final_test_metrics": final_test_metrics,
        }

    @classmethod
    def _stratified_split_indices(
        cls,
        labels: pd.Series,
        percentages: Sequence[int],
    ) -> List[List[Any]]:
        rng = random.Random(cls.RANDOM_STATE)
        partitions: List[List[Any]] = [[], [], []]
        weights = [percentage / 100 for percentage in percentages]

        for label in cls.LABELS:
            class_indices = list(labels.index[labels == label])
            if len(class_indices) < 3:
                raise ValueError(
                    f"Kelas {label} hanya memiliki {len(class_indices)} baris; "
                    "minimal 3 baris diperlukan agar muncul pada data latih, validasi, dan uji."
                )
            rng.shuffle(class_indices)
            ideals = [len(class_indices) * weight for weight in weights]
            allocations = [max(1, int(ideal)) for ideal in ideals]

            while sum(allocations) > len(class_indices):
                eligible = [index for index, count in enumerate(allocations) if count > 1]
                if not eligible:
                    raise ValueError(
                        f"Jumlah data kelas {label} tidak cukup untuk mewakili semua bagian."
                    )
                index = max(eligible, key=lambda item: allocations[item] - ideals[item])
                allocations[index] -= 1

            while sum(allocations) < len(class_indices):
                index = max(
                    range(len(allocations)),
                    key=lambda item: ideals[item] - allocations[item],
                )
                allocations[index] += 1

            offset = 0
            for partition_index, allocation in enumerate(allocations):
                partitions[partition_index].extend(
                    class_indices[offset : offset + allocation]
                )
                offset += allocation

        for partition in partitions:
            rng.shuffle(partition)
        return partitions

    @classmethod
    def _stratified_train_test_indices(
        cls,
        labels: pd.Series,
        train_percent: int,
        minimum_train_rows: int,
    ) -> List[List[Any]]:
        rng = random.Random(cls.RANDOM_STATE)
        train_indices: List[Any] = []
        test_indices: List[Any] = []
        class_indices_by_label: Dict[str, List[Any]] = {}

        for label in cls.LABELS:
            class_indices = list(labels.index[labels == label])
            if len(class_indices) < minimum_train_rows + 1:
                raise ValueError(
                    f"Kelas {label} hanya memiliki {len(class_indices)} baris; "
                    f"minimal {minimum_train_rows} baris latih dan 1 baris uji diperlukan."
                )
            rng.shuffle(class_indices)
            class_indices_by_label[label] = class_indices

        target_train_count = round(len(labels) * train_percent / 100)
        allocations = {
            label: max(
                minimum_train_rows,
                int(len(class_indices_by_label[label]) * train_percent / 100),
            )
            for label in cls.LABELS
        }
        max_train_counts = {
            label: len(class_indices_by_label[label]) - 1 for label in cls.LABELS
        }

        while sum(allocations.values()) < target_train_count:
            eligible = [
                label for label in cls.LABELS
                if allocations[label] < max_train_counts[label]
            ]
            if not eligible:
                break
            label = max(
                eligible,
                key=lambda item: (
                    len(class_indices_by_label[item]) * train_percent / 100 - allocations[item],
                    -cls.LABELS.index(item),
                ),
            )
            allocations[label] += 1

        while sum(allocations.values()) > target_train_count:
            eligible = [
                label for label in cls.LABELS
                if allocations[label] > minimum_train_rows
            ]
            if not eligible:
                break
            label = min(
                eligible,
                key=lambda item: (
                    len(class_indices_by_label[item]) * train_percent / 100 - allocations[item],
                    cls.LABELS.index(item),
                ),
            )
            allocations[label] -= 1

        for label in cls.LABELS:
            class_indices = class_indices_by_label[label]
            train_count = allocations[label]
            train_indices.extend(class_indices[:train_count])
            test_indices.extend(class_indices[train_count:])

        rng.shuffle(train_indices)
        rng.shuffle(test_indices)
        return [train_indices, test_indices]

    @classmethod
    def _build_model_pipeline(
        cls,
        numeric_columns: Sequence[str],
        categorical_columns: Sequence[str],
        classifier: Any,
        preprocessing: Dict[str, str],
    ) -> Pipeline:
        steps = []
        if preprocessing["outlier_handling"] == "iqr_cap":
            steps.append(("outlier_capper", _IQRCapper(list(numeric_columns))))
        steps.extend(
            [
                (
                    "preprocessing",
                    cls._build_preprocessor(
                        numeric_columns,
                        categorical_columns,
                        preprocessing["numeric_imputation"],
                        preprocessing["categorical_imputation"],
                        preprocessing["encoding"],
                        preprocessing["scaling"],
                    ),
                ),
                ("classifier", clone(classifier)),
            ]
        )
        return Pipeline(steps)

    @staticmethod
    def _set_knn_neighbors(pipeline: Pipeline, training_rows: int) -> None:
        classifier = pipeline.named_steps["classifier"]
        if isinstance(classifier, KNeighborsClassifier):
            classifier.set_params(n_neighbors=min(5, training_rows))

    @staticmethod
    def _drop_training_outliers(
        x_train: pd.DataFrame,
        y_train: pd.Series,
        numeric_columns: Sequence[str],
    ) -> tuple[pd.DataFrame, pd.Series, int]:
        if not numeric_columns:
            return x_train, y_train, 0

        outlier_mask = pd.Series(False, index=x_train.index)
        for column in numeric_columns:
            values = pd.to_numeric(x_train[column], errors="coerce")
            observed = values.dropna()
            if observed.empty:
                continue
            q1 = observed.quantile(0.25)
            q3 = observed.quantile(0.75)
            spread = q3 - q1
            outlier_mask |= values.lt(q1 - 1.5 * spread) | values.gt(q3 + 1.5 * spread)

        retained = ~outlier_mask
        return x_train.loc[retained], y_train.loc[retained], int(outlier_mask.sum())

    @classmethod
    def _ensure_training_classes(cls, labels: pd.Series, split_name: str) -> None:
        missing_classes = [label for label in cls.LABELS if label not in set(labels)]
        if missing_classes:
            raise ValueError(
                f"Setelah penanganan outlier, {split_name} tidak memiliki kelas "
                f"{', '.join(missing_classes)}. Ubah fitur atau metode preprocessing."
            )

    @classmethod
    def _calculate_metrics(
        cls,
        actual: pd.Series,
        predicted: Sequence[Any],
    ) -> Dict[str, float]:
        return {
            "accuracy": float(accuracy_score(actual, predicted)),
            "precision_macro": float(
                precision_score(
                    actual,
                    predicted,
                    labels=cls.LABELS,
                    average="macro",
                    zero_division=0,
                )
            ),
            "recall_macro": float(
                recall_score(
                    actual,
                    predicted,
                    labels=cls.LABELS,
                    average="macro",
                    zero_division=0,
                )
            ),
            "f1_macro": float(
                f1_score(
                    actual,
                    predicted,
                    labels=cls.LABELS,
                    average="macro",
                    zero_division=0,
                )
            ),
        }

    @staticmethod
    def _normalize_header(value: str) -> str:
        return "".join(character.lower() for character in value if character.isalnum())

    @classmethod
    def _is_target_column(cls, value: str) -> bool:
        return cls._normalize_header(value) in {"burnoutrisk", "burnoutlevel"}

    @classmethod
    def _find_target_column(cls, headers: Sequence[str]) -> Optional[str]:
        for expected in ("burnoutrisk", "burnoutlevel"):
            for header in headers:
                if cls._normalize_header(header) == expected:
                    return header
        return None

    @classmethod
    def _normalize_label(cls, value: Any) -> Optional[str]:
        if pd.isna(value):
            return None
        label = str(value).strip().lower()
        return {"low": "Low", "moderate": "Moderate", "high": "High"}.get(label)

    @staticmethod
    def _clean_value(value: Any) -> Any:
        if pd.isna(value):
            return None
        if isinstance(value, str):
            cleaned = value.strip()
            return cleaned if cleaned else None
        return value

    @staticmethod
    def _build_preprocessor(
        numeric_columns: Sequence[str],
        categorical_columns: Sequence[str],
        numeric_imputation: str,
        categorical_imputation: str,
        encoding: str,
        scaling: str,
    ) -> ColumnTransformer:
        transformers = []
        if numeric_columns:
            if numeric_imputation == "mean":
                numeric_imputer = SimpleImputer(
                    strategy="mean", keep_empty_features=True
                )
            elif numeric_imputation == "median":
                numeric_imputer = SimpleImputer(
                    strategy="median", keep_empty_features=True
                )
            elif numeric_imputation == "mode":
                numeric_imputer = SimpleImputer(
                    strategy="most_frequent", keep_empty_features=True
                )
            else:
                numeric_imputer = SimpleImputer(
                    strategy="constant", fill_value=0, keep_empty_features=True
                )
            numeric_steps = [("imputer", numeric_imputer)]
            if scaling == "minmax":
                numeric_steps.append(("scaler", MinMaxScaler()))
            elif scaling == "standard":
                numeric_steps.append(("scaler", StandardScaler()))
            transformers.append(
                (
                    "numeric",
                    Pipeline(numeric_steps),
                    list(numeric_columns),
                )
            )
        if categorical_columns:
            categorical_imputer = (
                SimpleImputer(
                    strategy="constant",
                    fill_value="Unknown",
                    keep_empty_features=True,
                )
                if categorical_imputation == "unknown"
                else SimpleImputer(
                    strategy="most_frequent", keep_empty_features=True
                )
            )
            encoder = (
                OneHotEncoder(handle_unknown="ignore")
                if encoding == "onehot"
                else OrdinalEncoder(
                    handle_unknown="use_encoded_value",
                    unknown_value=-1,
                )
            )
            transformers.append(
                (
                    "categorical",
                    Pipeline(
                        [
                            ("imputer", categorical_imputer),
                            ("encoder", encoder),
                        ]
                    ),
                    list(categorical_columns),
                )
            )
        return ColumnTransformer(transformers, sparse_threshold=0)
