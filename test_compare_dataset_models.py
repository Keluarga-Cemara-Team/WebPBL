import unittest

import pandas as pd
from sklearn.svm import SVC
from sklearn.preprocessing import OneHotEncoder

from app.core.use_cases.compare_dataset_models import (
    CompareDatasetModelsUseCase,
    _IQRCapper,
)


class CompareDatasetModelsUseCaseTests(unittest.TestCase):
    def setUp(self):
        self.use_case = CompareDatasetModelsUseCase()
        self.headers = ["Work_Hours", "Sleep_Quality", "Burnout_Risk"]
        self.rows = []
        for label, base_hours in (("Low", 30), ("Moderate", 42), ("High", 58)):
            for index in range(10):
                self.rows.append(
                    [
                        str(base_hours + index),
                        ("Good", "Average", "Poor")[("Low", "Moderate", "High").index(label)],
                        label,
                    ]
                )

    def test_trains_five_models_and_returns_evaluation_visualization_data(self):
        result = self.use_case.execute(
            {
                "headers": self.headers,
                "rows": self.rows,
                "feature_columns": ["Work_Hours", "Sleep_Quality"],
            }
        )

        self.assertEqual(len(result["results"]), 5)
        self.assertEqual(result["target_column"], "Burnout_Risk")
        self.assertEqual(result["rows_received"], 30)
        self.assertEqual(result["rows_used"], 30)
        self.assertEqual(
            result["train_rows"] + result["validation_rows"] + result["test_rows"],
            30,
        )
        self.assertEqual(result["split_percentages"], {"train": 70, "validation": 15, "test": 15})
        self.assertEqual(sum(result["actual_split_percentages"].values()), 100.0)
        self.assertEqual(result["class_distribution"], {"Low": 10, "Moderate": 10, "High": 10})
        self.assertIn("top_evaluated_model", result)
        for model_result in result["results"]:
            self.assertIn("validation_f1_macro", model_result)
        self.assertEqual(len(result["final_test_metrics"]["confusion_matrix"]), 3)
        self.assertEqual(result["final_test_model"], result["top_evaluated_model"])

    def test_stratified_split_keeps_all_classes_with_small_minority_class(self):
        labels = pd.Series(["Low"] * 11 + ["Moderate"] * 6 + ["High"] * 3)

        train_indices, validation_indices, test_indices = (
            self.use_case._stratified_split_indices(labels, (70, 15, 15))
        )

        for indices in (train_indices, validation_indices, test_indices):
            self.assertEqual(set(labels.loc[indices]), {"Low", "Moderate", "High"})
        self.assertEqual(
            [len(train_indices), len(validation_indices), len(test_indices)],
            [13, 4, 3],
        )

    def test_cross_validation_uses_training_split_for_selection_and_test_for_final_evaluation(self):
        result = self.use_case.execute(
            {
                "headers": self.headers,
                "rows": self.rows,
                "feature_columns": ["Work_Hours", "Sleep_Quality"],
                "train_percent": 80,
                "validation_percent": 0,
                "test_percent": 20,
                "validation_method": "cross_validation",
            }
        )

        self.assertEqual(result["validation_method"], "cross_validation")
        self.assertEqual(result["validation_folds"], 5)
        self.assertEqual(result["train_rows"], 24)
        self.assertEqual(result["validation_rows"], 0)
        self.assertEqual(result["test_rows"], 6)
        self.assertEqual(
            result["split_percentages"],
            {"train": 80, "validation": 0, "test": 20},
        )
        self.assertEqual(
            result["actual_split_percentages"],
            {"train": 80.0, "validation": 0.0, "test": 20.0},
        )
        self.assertEqual(result["final_test_model"], result["top_evaluated_model"])

    def test_cross_validation_split_matches_requested_ratio_for_uneven_class_sizes(self):
        labels = pd.Series(["Low"] * 23 + ["Moderate"] * 14 + ["High"] * 13)

        train_indices, test_indices = self.use_case._stratified_train_test_indices(
            labels, 80, 3
        )

        self.assertEqual((len(train_indices), len(test_indices)), (40, 10))
        for indices in (train_indices, test_indices):
            self.assertEqual(set(labels.loc[indices]), {"Low", "Moderate", "High"})

    def test_preprocessing_options_are_used_and_missing_drop_is_reported(self):
        rows = [row[:] for row in self.rows]
        rows[0][0] = ""

        result = self.use_case.execute(
            {
                "headers": self.headers,
                "rows": rows,
                "feature_columns": ["Work_Hours", "Sleep_Quality"],
                "preprocessing": {
                    "numeric_imputation": "drop",
                    "categorical_imputation": "unknown",
                    "outlier_handling": "iqr_cap",
                    "encoding": "onehot",
                    "scaling": "minmax",
                },
            }
        )

        self.assertEqual(result["missing_feature_rows_removed"], 1)
        self.assertEqual(result["rows_used"], 29)
        self.assertEqual(result["preprocessing"]["numeric_imputation"], "drop")
        self.assertEqual(result["preprocessing"]["categorical_imputation"], "unknown")
        self.assertEqual(result["preprocessing"]["outlier_handling"], "iqr_cap")
        self.assertEqual(result["preprocessing"]["encoding"], "onehot")
        self.assertEqual(result["preprocessing"]["scaling"], "minmax")

    def test_iqr_capper_learns_bounds_from_training_rows_only(self):
        training = pd.DataFrame({"Work_Hours": [1, 2, 3, 4, 5, 6, 7, 8]})
        held_out = pd.DataFrame({"Work_Hours": [100]})
        capper = _IQRCapper(["Work_Hours"]).fit(training)

        transformed = capper.transform(held_out)

        self.assertEqual(capper.bounds_["Work_Hours"], (-2.5, 11.5))
        self.assertEqual(transformed.loc[0, "Work_Hours"], 11.5)

    def test_outlier_drop_removes_training_rows_without_filtering_held_out_rows(self):
        training = pd.DataFrame({"Work_Hours": [1, 2, 3, 4, 5, 6, 7, 8, 100]})
        labels = pd.Series(
            ["Low", "Low", "Low", "Moderate", "Moderate", "Moderate", "High", "High", "High"]
        )
        held_out = pd.DataFrame({"Work_Hours": [10_000]})

        filtered_training, filtered_labels, removed = (
            self.use_case._drop_training_outliers(
                training, labels, ["Work_Hours"]
            )
        )

        self.assertEqual(removed, 1)
        self.assertEqual(len(filtered_training), 8)
        self.assertEqual(len(filtered_labels), 8)
        self.assertEqual(held_out.loc[0, "Work_Hours"], 10_000)

    def test_preprocessor_uses_selected_imputation_encoding_and_scaling(self):
        preprocessor = self.use_case._build_preprocessor(
            ["Work_Hours"],
            ["Sleep_Quality"],
            "mean",
            "unknown",
            "onehot",
            "minmax",
        )
        training = pd.DataFrame(
            {
                "Work_Hours": [1.0, None, 3.0],
                "Sleep_Quality": ["Good", None, "Poor"],
            }
        )

        transformed = preprocessor.fit_transform(training)

        self.assertEqual(transformed.shape, (3, 4))
        self.assertAlmostEqual(transformed[1, 0], 0.5)
        self.assertEqual(
            preprocessor.named_transformers_["categorical"]
            .named_steps["imputer"]
            .statistics_[0],
            "Unknown",
        )

    def test_model_pipeline_clips_outliers_and_applies_scaling(self):
        preprocessing = {
            "numeric_imputation": "mean",
            "categorical_imputation": "mode",
            "outlier_handling": "iqr_cap",
            "encoding": "onehot",
            "scaling": "standard",
        }
        pipeline = self.use_case._build_model_pipeline(
            ["Work_Hours"],
            ["Sleep_Quality"],
            SVC(),
            preprocessing,
        )
        training = pd.DataFrame(
            {
                "Work_Hours": [1, 2, 3, 4, 5, 6, 7, 8],
                "Sleep_Quality": ["Good", "Good", "Average", "Average", "Poor", "Poor", "Good", "Poor"],
            }
        )
        labels = pd.Series(["Low", "Low", "Low", "Moderate", "Moderate", "Moderate", "High", "High"])
        pipeline.fit(training, labels)

        transformed = pipeline.named_steps["outlier_capper"].transform(
            pd.DataFrame({"Work_Hours": [100], "Sleep_Quality": ["New category"]})
        )

        self.assertEqual(transformed.loc[0, "Work_Hours"], 11.5)
        self.assertIsInstance(
            pipeline.named_steps["preprocessing"]
            .named_transformers_["categorical"]
            .named_steps["encoder"],
            OneHotEncoder,
        )

    def test_rejects_missing_class_before_training(self):
        rows = [row for row in self.rows if row[-1] != "High"]

        with self.assertRaisesRegex(ValueError, "label Low, Moderate, dan High"):
            self.use_case.execute(
                {
                    "headers": self.headers,
                    "rows": rows,
                    "feature_columns": ["Work_Hours"],
                    "train_percent": 70,
                    "validation_percent": 15,
                    "test_percent": 15,
                }
            )

    def test_reports_per_class_counts_when_class_has_fewer_than_three_rows(self):
        rows = self.rows[:]
        rows = [row for row in rows if not (row[-1] == "Low" and int(row[0]) > 31)]

        with self.assertRaisesRegex(
            ValueError,
            r"Low: 2, Moderate: 10, High: 10.*Minimal 3 baris",
        ):
            self.use_case.execute(
                {
                    "headers": self.headers,
                    "rows": rows,
                    "feature_columns": ["Work_Hours"],
                }
            )

    def test_excludes_invalid_labels_and_duplicate_feature_target_rows(self):
        rows = self.rows + [
            ["", "Unknown", ""],
            self.rows[0],
        ]

        result = self.use_case.execute(
            {
                "headers": self.headers,
                "rows": rows,
                "feature_columns": ["Work_Hours", "Sleep_Quality"],
            }
        )

        self.assertEqual(result["invalid_label_rows_excluded"], 1)
        self.assertEqual(result["duplicate_rows_removed"], 1)
        self.assertEqual(result["rows_used"], 30)

    def test_rejects_target_as_a_feature(self):
        with self.assertRaisesRegex(ValueError, "target tidak boleh digunakan"):
            self.use_case.execute(
                {
                    "headers": self.headers,
                    "rows": self.rows,
                    "feature_columns": ["Work_Hours", "Burnout_Risk"],
                }
            )


if __name__ == "__main__":
    unittest.main()
