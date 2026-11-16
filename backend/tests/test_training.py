"""
backend/tests/test_training.py

Automated test suite verifying the Stage 2 baseline model training module:
- Verification of baseline model dictionary and hyperparameter defaults
- Full Pipeline assembly (ColumnTransformer + Classifier)
- Stratified 5-Fold Cross-Validation execution without data leakage
- Comprehensive test set evaluation (Accuracy, Macro F1, Weighted F1, Confusion Matrix)
- Reproducibility with fixed random seed
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
import pandas as pd
import numpy as np

from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression

from ml.src.preprocessing import (
    load_raw_dataset,
    prepare_features_and_target,
    split_data,
    PERFORMANCE_CATEGORIES,
)
from ml.src.train_models import (
    get_baseline_models,
    build_full_pipeline,
    run_cross_validation,
    evaluate_model_on_test,
    run_experiment,
)

MATH_CSV = PROJECT_ROOT / "ml" / "data" / "student-mat.csv"
POR_CSV = PROJECT_ROOT / "ml" / "data" / "student-por.csv"


def test_get_baseline_models():
    """Verify that baseline model catalog provides all required models."""
    models = get_baseline_models(random_state=42)

    assert "Logistic Regression (balanced)" in models
    assert "Logistic Regression (unweighted)" in models
    assert "Decision Tree (balanced)" in models
    assert "Decision Tree (unweighted)" in models
    assert "Random Forest (balanced)" in models
    assert "Random Forest (unweighted)" in models

    # Check that random seeds are properly set
    for name, model in models.items():
        assert hasattr(model, "random_state")
        assert model.random_state == 42


@pytest.mark.parametrize("scenario", ["A", "B"])
def test_build_full_pipeline(scenario):
    """Verify pipeline integrates preprocessor and classifier seamlessly."""
    model = LogisticRegression()
    pipeline = build_full_pipeline(scenario=scenario, classifier=model)

    assert isinstance(pipeline, Pipeline)
    assert "preprocessor" in pipeline.named_steps
    assert "classifier" in pipeline.named_steps


def test_cross_validation_execution():
    """Verify Stratified K-Fold cross-validation produces expected metrics structure."""
    df = load_raw_dataset(MATH_CSV)
    X, y = prepare_features_and_target(df, scenario="A")
    X_train, _, y_train, _ = split_data(X, y, test_size=0.20, random_state=42)

    # Test with 2 fast baseline models
    test_models = {
        "LR": LogisticRegression(max_iter=200, random_state=42),
        "DT": LogisticRegression(max_iter=200, random_state=42),
    }

    cv_df = run_cross_validation(
        X_train, y_train, scenario="A", models=test_models, cv_splits=3, random_state=42
    )

    assert isinstance(cv_df, pd.DataFrame)
    assert len(cv_df) == 2
    for col in ["model_name", "macro_f1_mean", "macro_f1_std", "accuracy_mean", "weighted_f1_mean"]:
        assert col in cv_df.columns

    # Verify score ranges
    assert 0.0 <= cv_df["macro_f1_mean"].iloc[0] <= 1.0
    assert 0.0 <= cv_df["accuracy_mean"].iloc[0] <= 1.0


def test_evaluate_model_on_test():
    """Verify test evaluation generates complete metrics and 4x4 confusion matrix."""
    df = load_raw_dataset(MATH_CSV)
    X, y = prepare_features_and_target(df, scenario="A")
    X_train, X_test, y_train, y_test = split_data(X, y, test_size=0.20, random_state=42)

    pipeline = build_full_pipeline(
        scenario="A",
        classifier=LogisticRegression(max_iter=500, random_state=42),
    )

    eval_results = evaluate_model_on_test(pipeline, X_train, y_train, X_test, y_test)

    assert "test_accuracy" in eval_results
    assert "test_macro_f1" in eval_results
    assert "test_weighted_f1" in eval_results
    assert "confusion_matrix_df" in eval_results
    assert "classification_report_text" in eval_results

    cm_df = eval_results["confusion_matrix_df"]
    assert cm_df.shape == (4, 4)
    # Sum of confusion matrix elements must match test set size (79 in Math)
    assert cm_df.values.sum() == len(X_test)


def test_run_experiment_end_to_end():
    """Verify end-to-end execution of a complete experiment."""
    res = run_experiment(MATH_CSV, scenario="A", random_state=42)

    assert res["scenario"] == "A"
    assert res["X_train_shape"] == (316, 30)
    assert res["X_test_shape"] == (79, 30)
    assert res["best_candidate_name"] in get_baseline_models()
    assert 0.0 <= res["test_evaluation"]["test_accuracy"] <= 1.0


def test_reproducibility():
    """Verify that runs with identical random seed yield identical results."""
    res1 = run_experiment(MATH_CSV, scenario="A", random_state=42)
    res2 = run_experiment(MATH_CSV, scenario="A", random_state=42)

    assert res1["test_evaluation"]["test_accuracy"] == res2["test_evaluation"]["test_accuracy"]
    assert res1["test_evaluation"]["test_macro_f1"] == res2["test_evaluation"]["test_macro_f1"]
