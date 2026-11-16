"""
backend/tests/test_mca_ml_pipeline.py

Comprehensive automated test suite for Phase 3A: MCA Machine Learning Training Pipeline
using Synthetic Prototype Datasets.

Verifies:
1. Synthetic dataset loading, schemas, validation reports, and class distributions.
2. Strict data leakage prevention (synthetic final scores and identifiers excluded from features).
3. Student-group-aware train/test separation (GroupShuffleSplit with zero student overlap).
4. Feature compatibility audit and Phase 2E point-in-time extraction payload adapters.
5. Multi-model training and evaluation metrics (Accuracy, Balanced Accuracy, Macro F1, Per-Class, CM).
6. Exported pipeline artifacts (.joblib and metadata .json) integrity and disclaimers.
7. Reusable prediction interface (single and batch, probabilities, confidence, error handling).
8. Strict isolation of Phase 1 UCI pipelines and database tables (zero MySQL/ORM modifications).
"""

import json
from pathlib import Path
import pytest
import numpy as np
import pandas as pd

import ml.src.mca_compat  # Safe sklearn C-extension handling on Windows

from ml.src.mca_dataset_loader import (
    load_semester_level_dataset,
    load_subject_level_dataset,
    validate_dataset_schema,
)
from ml.src.mca_feature_adapter import (
    SEMESTER_LEVEL_AUDIT,
    SUBJECT_LEVEL_AUDIT,
    adapt_phase2e_semester_payload,
    adapt_phase2e_subject_payload,
    get_feature_compatibility_audit,
)
from ml.src.mca_trainer import (
    SYNTHETIC_DISCLAIMER,
    build_preprocessor,
    evaluate_classifier,
    split_dataset_by_student_group,
    train_semester_level_pipelines,
    train_subject_level_pipelines,
)
from ml.src.mca_predictor import (
    SYNTHETIC_WARNING,
    batch_predict_semester_performance,
    batch_predict_subject_performance,
    get_model_metadata,
    load_semester_model,
    load_subject_model,
    predict_semester_performance,
    predict_subject_performance,
)


# ===========================================================================
# 1. Dataset Loading & Validation Tests
# ===========================================================================

def test_load_subject_level_dataset_schema():
    """Verify subject-level synthetic dataset loads with exact rows, columns, and valid tiers."""
    df, report = load_subject_level_dataset(validate=True)

    assert len(df) == 6370
    assert df.shape[1] == 30
    assert report["total_rows"] == 6370
    assert report["total_columns"] == 30
    assert report["unique_students"] == 1200
    assert df["performance_tier"].isna().sum() == 0
    assert df["student_id"].isna().sum() == 0
    assert len(report["null_counts"]) > 0  # Expected missingness in course-type-specific and prior semester fields

    expected_tiers = {"Excellent", "Good", "Average", "Needs Improvement"}
    assert set(report["performance_tier_distribution"].keys()) == expected_tiers

    expected_types = {"theory", "lab", "elective", "project"}
    assert set(report["course_type_distribution"].keys()) == expected_types

    # Ensure required columns are present in DataFrame
    assert "synthetic_final_score" in df.columns
    assert "performance_tier" in df.columns
    assert "student_id" in df.columns
    assert "course_type" in df.columns


def test_load_semester_level_dataset_schema():
    """Verify semester-level synthetic dataset loads with exact rows, columns, and valid tiers."""
    df, report = load_semester_level_dataset(validate=True)

    assert len(df) == 1200
    assert df.shape[1] == 28
    assert report["total_rows"] == 1200
    assert report["total_columns"] == 28
    assert report["unique_students"] == 1200
    assert df["performance_tier"].isna().sum() == 0
    assert df["student_id"].isna().sum() == 0
    assert len(report["null_counts"]) > 0  # Expected missingness in prior semester and project/lab summary fields

    expected_tiers = {"Excellent", "Good", "Average", "Needs Improvement"}
    assert set(report["performance_tier_distribution"].keys()) == expected_tiers

    assert "synthetic_semester_final_score" in df.columns
    assert "performance_tier" in df.columns
    assert "student_id" in df.columns


# ===========================================================================
# 2. Leakage Prevention Tests
# ===========================================================================

def test_leakage_prevention_subject_level():
    """Verify target score columns and student identifiers are strictly excluded from input features."""
    supported = SUBJECT_LEVEL_AUDIT["supported_features"]
    targets = SUBJECT_LEVEL_AUDIT["target_outcome_columns"]
    identifiers = SUBJECT_LEVEL_AUDIT["identifier_metadata_columns"]

    # Target final score MUST NOT be in model input features
    assert "synthetic_final_score" not in supported
    assert "synthetic_final_score" in targets

    # Target tier MUST NOT be in input features
    assert "performance_tier" not in supported
    assert "performance_tier" in targets

    # Identifiers MUST NOT be in model input features
    for col in identifiers:
        assert col not in supported


def test_leakage_prevention_semester_level():
    """Verify semester-level target score columns and identifiers are strictly excluded from input features."""
    supported = SEMESTER_LEVEL_AUDIT["supported_features"]
    targets = SEMESTER_LEVEL_AUDIT["target_outcome_columns"]
    identifiers = SEMESTER_LEVEL_AUDIT["identifier_metadata_columns"]

    assert "synthetic_semester_final_score" not in supported
    assert "synthetic_semester_final_score" in targets

    assert "performance_tier" not in supported
    assert "performance_tier" in targets

    for col in identifiers:
        assert col not in supported


# ===========================================================================
# 3. Student Group Split Isolation Tests
# ===========================================================================

def test_group_shuffle_split_isolation():
    """Verify student-group-aware split guarantees zero student_id overlap between train and test."""
    df, _ = load_subject_level_dataset(validate=False)
    feature_cols = SUBJECT_LEVEL_AUDIT["supported_features"]

    X_train, X_test, y_train, y_test, g_train, g_test = split_dataset_by_student_group(
        df=df,
        feature_cols=feature_cols,
        target_col="performance_tier",
        group_col="student_id",
        test_size=0.2,
        random_state=42,
    )

    train_students = set(g_train)
    test_students = set(g_test)

    # 1. Complete student isolation
    overlap = train_students.intersection(test_students)
    assert len(overlap) == 0, f"Leakage detected! Overlapping students: {overlap}"

    # 2. Proper proportion
    total_students = len(train_students) + len(test_students)
    assert total_students == 1200
    assert len(test_students) == 240
    assert len(train_students) == 960

    # 3. Shape alignment
    assert len(X_train) == len(y_train) == len(g_train)
    assert len(X_test) == len(y_test) == len(g_test)
    assert len(X_train) + len(X_test) == len(df)


# ===========================================================================
# 4. Feature Compatibility Audit & Adapter Tests
# ===========================================================================

def test_feature_compatibility_audit_structure():
    """Verify formal feature compatibility audit report structure and content."""
    audit = get_feature_compatibility_audit()
    assert "subject_level" in audit
    assert "semester_level" in audit
    assert "summary" in audit

    assert len(audit["subject_level"]["supported_features"]) == 14
    assert len(audit["subject_level"]["synthetic_only_features"]) == 6
    assert len(audit["semester_level"]["supported_features"]) == 8
    assert len(audit["semester_level"]["synthetic_only_features"]) == 13


def test_feature_adapter_subject_payload():
    """Verify Phase 2E subject feature extraction output adapts seamlessly to model input."""
    # Mock Phase 2E extraction dictionary
    mock_payload = {
        "metadata": {
            "student_id": 1,
            "session_course_id": 10,
            "target_semester": 1,
            "course_code": "MCA108",
            "course_type": "theory",
            "cutoff_timestamp": "2026-11-13T00:00:00Z",
        },
        "features": {
            "attendance_percentage": 88.5,
            "mst1_marks": 17.5,
            "mst2_marks": 18.0,
            "assignment_score": 9.0,
            "viva_marks": None,
            "lab_record_score": None,
            "synopsis_approved": None,
            "design_score": None,
            "implementation_pct": None,
            "supervisor_score": None,
            "latest_prior_sgpa": 8.1,
            "latest_declared_cgpa": 7.9,
        },
    }

    adapted_df = adapt_phase2e_subject_payload(mock_payload)

    assert isinstance(adapted_df, pd.DataFrame)
    assert len(adapted_df) == 1
    assert list(adapted_df.columns) == SUBJECT_LEVEL_AUDIT["supported_features"]

    row = adapted_df.iloc[0]
    assert row["semester_number"] == 1
    assert row["course_type"] == "theory"
    assert row["attendance_percentage"] == 88.5
    assert row["mst1_marks"] == 17.5
    assert row["mst2_marks"] == 18.0
    assert row["assignment_marks"] == 9.0
    assert row["prior_sgpa"] == 8.1
    assert row["prior_cgpa"] == 7.9


def test_feature_adapter_semester_payload():
    """Verify Phase 2E semester feature extraction output adapts seamlessly to model input."""
    mock_payload = {
        "metadata": {
            "student_id": 1,
            "academic_session_id": 2,
            "target_semester": 1,
            "cutoff_timestamp": "2026-11-13T00:00:00Z",
        },
        "features": {
            "total_enrolled_courses": 7,
            "average_attendance_percentage": 82.0,
            "average_mst1_marks": 16.5,
            "average_mst2_marks": 17.0,
            "average_assignment_score": 8.5,
            "latest_prior_sgpa": 7.8,
            "latest_declared_cgpa": 7.6,
        },
    }

    adapted_df = adapt_phase2e_semester_payload(mock_payload)

    assert isinstance(adapted_df, pd.DataFrame)
    assert len(adapted_df) == 1
    assert list(adapted_df.columns) == SEMESTER_LEVEL_AUDIT["supported_features"]

    row = adapted_df.iloc[0]
    assert row["semester_number"] == 1
    assert row["courses_included"] == 7
    assert row["mean_attendance_percentage"] == 82.0
    assert row["mean_mst1_marks"] == 16.5
    assert row["mean_mst2_marks"] == 17.0
    assert row["mean_assignment_marks"] == 8.5
    assert row["mean_prior_sgpa"] == 7.8
    assert row["mean_prior_cgpa"] == 7.6


# ===========================================================================
# 5. Pipeline Preprocessing & Evaluation Tests
# ===========================================================================

def test_build_preprocessor_execution():
    """Verify ColumnTransformer handles numerical imputation/scaling and categorical encoding without leakage."""
    preprocessor = build_preprocessor(
        numeric_features=["attendance_percentage", "mst1_marks"],
        categorical_features=["course_type"],
    )

    train_data = pd.DataFrame({
        "attendance_percentage": [80.0, np.nan, 90.0, 75.0],
        "mst1_marks": [15.0, 18.0, np.nan, 12.0],
        "course_type": ["theory", "lab", "theory", "project"],
    })

    transformed = preprocessor.fit_transform(train_data)
    assert isinstance(transformed, np.ndarray)
    assert transformed.shape[0] == 4
    # 2 numerical scaled features + 3 one-hot categories = 5 columns
    assert transformed.shape[1] == 5
    # No NaNs in transformed output
    assert not np.isnan(transformed).any()


def test_evaluate_classifier_metrics():
    """Verify evaluate_classifier computes all required classification metrics."""
    from sklearn.dummy import DummyClassifier
    from sklearn.pipeline import Pipeline

    X_train = pd.DataFrame({"feat1": [1.0, 2.0, 3.0, 4.0]})
    y_train = pd.Series(["Good", "Good", "Average", "Good"])
    X_test = pd.DataFrame({"feat1": [2.0, 3.0]})
    y_test = pd.Series(["Good", "Average"])
    classes = ["Average", "Good"]

    pipe = Pipeline([("clf", DummyClassifier(strategy="most_frequent"))])
    pipe.fit(X_train, y_train)

    metrics = evaluate_classifier(pipe, X_train, y_train, X_test, y_test, classes)

    assert "accuracy" in metrics
    assert "balanced_accuracy" in metrics
    assert "macro_precision" in metrics
    assert "macro_recall" in metrics
    assert "macro_f1" in metrics
    assert "per_class" in metrics
    assert "confusion_matrix" in metrics
    assert len(metrics["confusion_matrix"]) == 2


# ===========================================================================
# 6. Saved Artifacts Integrity Tests
# ===========================================================================

def test_subject_level_artifact_integrity():
    """Verify saved subject-level pipeline joblib and metadata JSON exist and are valid."""
    pipeline, meta = load_subject_model(force_reload=True)

    assert pipeline is not None
    assert hasattr(pipeline, "predict")
    assert hasattr(pipeline, "predict_proba")

    assert meta["scope"] == "subject_level"
    assert meta["dataset_type"] == "synthetic_prototype"
    assert SYNTHETIC_DISCLAIMER in meta["synthetic_data_disclaimer"]
    assert meta["total_rows"] == 6370
    assert meta["train_rows"] == 5066
    assert meta["test_rows"] == 1304
    assert meta["train_unique_students"] == 960
    assert meta["test_unique_students"] == 240

    assert "selected_algorithm" in meta
    assert "selected_macro_f1" in meta
    assert meta["selected_macro_f1"] > 0.50

    # Ensure all 4 algorithms were evaluated
    comparison = meta["all_models_comparison"]
    assert "Majority Baseline" in comparison
    assert "Logistic Regression" in comparison
    assert "Decision Tree" in comparison
    assert "Random Forest" in comparison


def test_semester_level_artifact_integrity():
    """Verify saved semester-level pipeline joblib and metadata JSON exist and are valid."""
    pipeline, meta = load_semester_model(force_reload=True)

    assert pipeline is not None
    assert hasattr(pipeline, "predict")
    assert hasattr(pipeline, "predict_proba")

    assert meta["scope"] == "semester_level"
    assert meta["dataset_type"] == "synthetic_prototype"
    assert SYNTHETIC_DISCLAIMER in meta["synthetic_data_disclaimer"]
    assert meta["total_rows"] == 1200
    assert meta["train_rows"] == 960
    assert meta["test_rows"] == 240

    assert "selected_algorithm" in meta
    assert "selected_macro_f1" in meta
    assert meta["selected_macro_f1"] > 0.50

    comparison = meta["all_models_comparison"]
    assert "Majority Baseline" in comparison
    assert "Logistic Regression" in comparison
    assert "Decision Tree" in comparison
    assert "Random Forest" in comparison


# ===========================================================================
# 7. Prediction Interface Tests
# ===========================================================================

def test_predictor_subject_prediction_with_raw_dict():
    """Verify predict_subject_performance works with a raw dictionary input."""
    payload = {
        "semester_number": 1,
        "course_type": "theory",
        "attendance_percentage": 88.0,
        "mst1_marks": 18.0,
        "mst2_marks": 17.5,
        "assignment_marks": 9.0,
        "prior_sgpa": 8.5,
        "prior_cgpa": 8.3,
    }

    result = predict_subject_performance(payload)

    assert result["scope"] == "subject_level"
    assert result["predicted_tier"] in {"Excellent", "Good", "Average", "Needs Improvement"}
    assert 0.0 <= result["confidence"] <= 1.0
    assert isinstance(result["probabilities"], dict)
    assert len(result["probabilities"]) == 4

    prob_sum = sum(result["probabilities"].values())
    assert abs(prob_sum - 1.0) < 0.01

    assert result["model_metadata"]["is_synthetic"] is True
    assert SYNTHETIC_WARNING in result["synthetic_data_warning"]
    assert "attendance_percentage" in result["compatibility_status"]["used_features"]


def test_predictor_subject_prediction_with_phase2e_payload():
    """Verify predict_subject_performance handles Phase 2E extraction payload format."""
    payload = {
        "metadata": {
            "student_id": 10,
            "session_course_id": 101,
            "target_semester": 1,
            "course_code": "MCA108",
            "course_type": "theory",
            "cutoff_timestamp": "2026-11-13T00:00:00Z",
        },
        "features": {
            "attendance_percentage": 45.0,
            "mst1_marks": 8.0,
            "mst2_marks": 7.0,
            "assignment_score": 4.0,
            "viva_marks": None,
            "lab_record_score": None,
            "synopsis_approved": None,
            "design_score": None,
            "implementation_pct": None,
            "supervisor_score": None,
            "latest_prior_sgpa": 5.0,
            "latest_declared_cgpa": 5.2,
        },
    }

    result = predict_subject_performance(payload)

    assert result["scope"] == "subject_level"
    assert result["predicted_tier"] in {"Excellent", "Good", "Average", "Needs Improvement"}
    assert result["confidence"] > 0.0
    assert result["compatibility_status"]["payload_format"] == "phase_2e_extraction"


def test_predictor_semester_prediction_with_raw_dict():
    """Verify predict_semester_performance works with raw dictionary input."""
    payload = {
        "semester_number": 1,
        "courses_included": 7,
        "mean_attendance_percentage": 75.0,
        "mean_mst1_marks": 15.0,
        "mean_mst2_marks": 14.5,
        "mean_assignment_marks": 8.0,
        "mean_prior_sgpa": 7.5,
        "mean_prior_cgpa": 7.4,
    }

    result = predict_semester_performance(payload)

    assert result["scope"] == "semester_level"
    assert result["predicted_tier"] in {"Excellent", "Good", "Average", "Needs Improvement"}
    assert 0.0 <= result["confidence"] <= 1.0
    assert len(result["probabilities"]) == 4

    prob_sum = sum(result["probabilities"].values())
    assert abs(prob_sum - 1.0) < 0.01

    assert result["model_metadata"]["is_synthetic"] is True
    assert SYNTHETIC_WARNING in result["synthetic_data_warning"]


def test_predictor_semester_prediction_with_phase2e_payload():
    """Verify predict_semester_performance handles Phase 2E extraction payload format."""
    payload = {
        "metadata": {
            "student_id": 15,
            "academic_session_id": 2,
            "target_semester": 1,
            "cutoff_timestamp": "2026-11-13T00:00:00Z",
        },
        "features": {
            "total_enrolled_courses": 7,
            "average_attendance_percentage": 92.0,
            "average_mst1_marks": 19.0,
            "average_mst2_marks": 18.5,
            "average_assignment_score": 9.5,
            "latest_prior_sgpa": 9.2,
            "latest_declared_cgpa": 9.0,
        },
    }

    result = predict_semester_performance(payload)

    assert result["scope"] == "semester_level"
    assert result["predicted_tier"] in {"Excellent", "Good", "Average", "Needs Improvement"}
    assert result["confidence"] > 0.0
    assert result["compatibility_status"]["payload_format"] == "phase_2e_extraction"


def test_batch_prediction_helpers():
    """Verify batch_predict helpers return correct lists of prediction dicts."""
    subj_payloads = [
        {"semester_number": 1, "course_type": "theory", "attendance_percentage": 90.0, "mst1_marks": 18.0},
        {"semester_number": 1, "course_type": "lab", "attendance_percentage": 45.0, "mst1_marks": 6.0},
    ]
    subj_results = batch_predict_subject_performance(subj_payloads)
    assert len(subj_results) == 2
    assert all("predicted_tier" in r for r in subj_results)

    sem_payloads = [
        {"semester_number": 1, "courses_included": 7, "mean_attendance_percentage": 85.0},
        {"semester_number": 1, "courses_included": 7, "mean_attendance_percentage": 50.0},
    ]
    sem_results = batch_predict_semester_performance(sem_payloads)
    assert len(sem_results) == 2
    assert all("predicted_tier" in r for r in sem_results)


def test_predictor_error_handling():
    """Verify predictor raises informative errors on invalid input payloads."""
    with pytest.raises(ValueError, match="Payload cannot be empty"):
        predict_subject_performance({})

    with pytest.raises(TypeError, match="Payload must be a dict or pd.DataFrame"):
        predict_subject_performance("invalid_payload_type")  # type: ignore

    with pytest.raises(ValueError, match="Payload cannot be empty"):
        predict_semester_performance({})

    with pytest.raises(TypeError, match="Payload must be a dict or pd.DataFrame"):
        predict_semester_performance([1, 2, 3])  # type: ignore

    with pytest.raises(ValueError, match="Unknown scope"):
        get_model_metadata("invalid_scope")


# ===========================================================================
# 8. Phase 1 UCI Isolation & Non-Destructive Boundary Tests
# ===========================================================================

def test_phase1_uci_infrastructure_isolated():
    """Verify Phase 1 ML artifacts, datasets, and training code are strictly intact and unmodified."""
    from app.models import Student, PredictionRecord  # Phase 1 ORM models
    assert Student is not None
    assert PredictionRecord is not None

    root = Path(__file__).resolve().parent.parent.parent
    uci_models = [
        root / "ml/models/student_mat_scenario_a_logistic_regression.joblib",
        root / "ml/models/student_mat_scenario_b_decision_tree.joblib",
        root / "ml/models/student_por_scenario_a_random_forest.joblib",
        root / "ml/models/student_por_scenario_b_decision_tree.joblib",
    ]
    for m in uci_models:
        assert m.exists(), f"Phase 1 model artifact must remain intact: {m}"

    uci_training = root / "ml/src/train_models.py"
    assert uci_training.exists(), "Phase 1 training script must remain intact"

    # Verify Phase 1 training script has not been modified to reference MCA
    content = uci_training.read_text(encoding="utf-8")
    assert "mca" not in content.lower(), "Phase 1 training script must remain clean of MCA references"
