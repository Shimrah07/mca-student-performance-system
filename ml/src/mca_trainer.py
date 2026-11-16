"""
ml/src/mca_trainer.py

MCA Machine Learning Training Pipeline using Synthetic Prototype Datasets.
Trains, evaluates, and exports reproducible classification pipelines for
both subject-level and semester-level prediction scopes.

Guarantees:
- Strict student-group-aware train/test separation (GroupShuffleSplit).
- Strict leakage prevention: target-only outcome columns and identifiers excluded.
- Preprocessing fit strictly on training folds via sklearn Pipeline.
- Compares Majority Baseline, Logistic Regression, Decision Tree, and Random Forest.
- Comprehensive evaluation: Accuracy, Balanced Accuracy, Macro F1, Per-Class metrics, Confusion Matrix.
- Saves model artifacts and full audit metadata to ml/artifacts/mca/.
- Preserves explicit synthetic disclaimer in all artifacts and metadata.
"""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import ml.src.mca_compat  # Ensure sklearn C-extension stubs if restricted by OS

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

from ml.src.mca_dataset_loader import (
    load_semester_level_dataset,
    load_subject_level_dataset,
)
from ml.src.mca_feature_adapter import (
    SEMESTER_LEVEL_AUDIT,
    SUBJECT_LEVEL_AUDIT,
)

ARTIFACTS_DIR = Path("ml/artifacts/mca")
SYNTHETIC_DISCLAIMER = (
    "This model was trained exclusively on synthetic/prototype data (Phase 3A). "
    "It is NOT trained on real UIT-RGPV student records, does NOT reflect actual "
    "institutional grading regulations, and must NOT be represented as real academic accuracy."
)


# ===========================================================================
# Split & Preprocessor Builders
# ===========================================================================

def split_dataset_by_student_group(
    df: pd.DataFrame,
    feature_cols: List[str],
    target_col: str = "performance_tier",
    group_col: str = "student_id",
    test_size: float = 0.2,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, np.ndarray, np.ndarray]:
    """
    Perform a student-group-aware train/test split.
    Records for any single student_id appear exclusively in train OR test, never both.
    """
    gss = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
    groups = df[group_col].values

    train_idx, test_idx = next(gss.split(df, df[target_col], groups=groups))

    X = df[feature_cols]
    y = df[target_col]

    X_train, X_test = X.iloc[train_idx].copy(), X.iloc[test_idx].copy()
    y_train, y_test = y.iloc[train_idx].copy(), y.iloc[test_idx].copy()
    groups_train, groups_test = groups[train_idx], groups[test_idx]

    # Verify 100% group isolation
    train_students = set(groups_train)
    test_students = set(groups_test)
    overlap = train_students.intersection(test_students)
    if overlap:
        raise ValueError(f"Student data leakage detected! Overlapping students: {len(overlap)}")

    return X_train, X_test, y_train, y_test, groups_train, groups_test


def build_preprocessor(
    numeric_features: List[str],
    categorical_features: List[str],
) -> ColumnTransformer:
    """Build a ColumnTransformer with numerical median imputation/scaling and categorical encoding."""
    transformers = []

    if numeric_features:
        num_pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ])
        transformers.append(("num", num_pipeline, numeric_features))

    if categorical_features:
        cat_pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ])
        transformers.append(("cat", cat_pipeline, categorical_features))

    return ColumnTransformer(transformers=transformers, remainder="drop")


# ===========================================================================
# Model Evaluation
# ===========================================================================

def evaluate_classifier(
    pipeline: Pipeline,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    classes: List[str],
) -> Dict[str, Any]:
    """Calculate and return all required classification metrics on test split."""
    y_pred = pipeline.predict(X_test)

    acc = float(accuracy_score(y_test, y_pred))
    bal_acc = float(balanced_accuracy_score(y_test, y_pred))
    prec_macro = float(precision_score(y_test, y_pred, average="macro", zero_division=0))
    rec_macro = float(recall_score(y_test, y_pred, average="macro", zero_division=0))
    f1_macro = float(f1_score(y_test, y_pred, average="macro", zero_division=0))

    report_dict = classification_report(y_test, y_pred, labels=classes, output_dict=True, zero_division=0)
    cm = confusion_matrix(y_test, y_pred, labels=classes).tolist()

    return {
        "accuracy": round(acc, 4),
        "balanced_accuracy": round(bal_acc, 4),
        "macro_precision": round(prec_macro, 4),
        "macro_recall": round(rec_macro, 4),
        "macro_f1": round(f1_macro, 4),
        "per_class": {
            cls: {
                "precision": round(report_dict[cls]["precision"], 4),
                "recall": round(report_dict[cls]["recall"], 4),
                "f1-score": round(report_dict[cls]["f1-score"], 4),
                "support": int(report_dict[cls]["support"]),
            }
            for cls in classes if cls in report_dict
        },
        "confusion_matrix": cm,
        "classes": classes,
    }


# ===========================================================================
# Subject-Level Pipeline Training
# ===========================================================================

def train_subject_level_pipelines(
    csv_path: Optional[str] = None,
    random_state: int = 42,
    save_artifacts: bool = True,
) -> Dict[str, Any]:
    """
    Train and evaluate subject-level classification pipelines on supported Phase 2E features.
    """
    df, val_report = load_subject_level_dataset(csv_path=csv_path, validate=True)

    feature_cols = SUBJECT_LEVEL_AUDIT["supported_features"]
    numeric_cols = [c for c in feature_cols if c != "course_type"]
    categorical_cols = ["course_type"]
    classes = sorted(list(val_report["performance_tier_distribution"].keys()))

    X_train, X_test, y_train, y_test, g_train, g_test = split_dataset_by_student_group(
        df=df,
        feature_cols=feature_cols,
        target_col="performance_tier",
        group_col="student_id",
        test_size=0.2,
        random_state=random_state,
    )

    models = {
        "Majority Baseline": DummyClassifier(strategy="most_frequent"),
        "Logistic Regression": LogisticRegression(
            solver="lbfgs",
            max_iter=1000,
            random_state=random_state,
        ),
        "Decision Tree": DecisionTreeClassifier(
            max_depth=6,
            min_samples_leaf=10,
            random_state=random_state,
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=100,
            max_depth=8,
            min_samples_leaf=5,
            random_state=random_state,
        ),
    }

    results = {}
    best_name = None
    best_f1 = -1.0
    best_pipeline = None

    for name, clf in models.items():
        preprocessor = build_preprocessor(numeric_cols, categorical_cols)
        pipeline = Pipeline([
            ("preprocessor", preprocessor),
            ("classifier", clf),
        ])

        pipeline.fit(X_train, y_train)
        metrics = evaluate_classifier(pipeline, X_train, y_train, X_test, y_test, classes)
        results[name] = metrics

        if metrics["macro_f1"] > best_f1:
            best_f1 = metrics["macro_f1"]
            best_name = name
            best_pipeline = pipeline

    train_dist = y_train.value_counts().to_dict()
    test_dist = y_test.value_counts().to_dict()

    metadata = {
        "scope": "subject_level",
        "dataset_type": "synthetic_prototype",
        "dataset_version": "2026-11-13",
        "synthetic_data_disclaimer": SYNTHETIC_DISCLAIMER,
        "training_timestamp": datetime.now(timezone.utc).isoformat(),
        "total_rows": len(df),
        "train_rows": len(X_train),
        "test_rows": len(X_test),
        "train_unique_students": int(len(set(g_train))),
        "test_unique_students": int(len(set(g_test))),
        "target_classes": classes,
        "feature_names": feature_cols,
        "numeric_features": numeric_cols,
        "categorical_features": categorical_cols,
        "train_class_distribution": train_dist,
        "test_class_distribution": test_dist,
        "selected_algorithm": best_name,
        "selected_macro_f1": best_f1,
        "evaluation_metrics": results[best_name],
        "all_models_comparison": {k: {m: v[m] for m in ["accuracy", "balanced_accuracy", "macro_f1"]} for k, v in results.items()},
        "train_test_split_method": "GroupShuffleSplit(student_id, test_size=0.2)",
        "random_seed": random_state,
    }

    if save_artifacts:
        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        model_path = ARTIFACTS_DIR / "subject_level_pipeline.joblib"
        meta_path = ARTIFACTS_DIR / "subject_level_metadata.json"

        joblib.dump(best_pipeline, model_path)
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

    return {
        "best_algorithm": best_name,
        "best_pipeline": best_pipeline,
        "results": results,
        "metadata": metadata,
    }


# ===========================================================================
# Semester-Level Pipeline Training
# ===========================================================================

def train_semester_level_pipelines(
    csv_path: Optional[str] = None,
    random_state: int = 42,
    save_artifacts: bool = True,
) -> Dict[str, Any]:
    """
    Train and evaluate semester-level classification pipelines on supported Phase 2E features.
    """
    df, val_report = load_semester_level_dataset(csv_path=csv_path, validate=True)

    feature_cols = SEMESTER_LEVEL_AUDIT["supported_features"]
    numeric_cols = feature_cols.copy()  # All semester-level supported features are numerical
    categorical_cols = []
    classes = sorted(list(val_report["performance_tier_distribution"].keys()))

    X_train, X_test, y_train, y_test, g_train, g_test = split_dataset_by_student_group(
        df=df,
        feature_cols=feature_cols,
        target_col="performance_tier",
        group_col="student_id",
        test_size=0.2,
        random_state=random_state,
    )

    models = {
        "Majority Baseline": DummyClassifier(strategy="most_frequent"),
        "Logistic Regression": LogisticRegression(
            solver="lbfgs",
            max_iter=1000,
            random_state=random_state,
        ),
        "Decision Tree": DecisionTreeClassifier(
            max_depth=5,
            min_samples_leaf=5,
            random_state=random_state,
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=100,
            max_depth=6,
            min_samples_leaf=3,
            random_state=random_state,
        ),
    }

    results = {}
    best_name = None
    best_f1 = -1.0
    best_pipeline = None

    for name, clf in models.items():
        preprocessor = build_preprocessor(numeric_cols, categorical_cols)
        pipeline = Pipeline([
            ("preprocessor", preprocessor),
            ("classifier", clf),
        ])

        pipeline.fit(X_train, y_train)
        metrics = evaluate_classifier(pipeline, X_train, y_train, X_test, y_test, classes)
        results[name] = metrics

        if metrics["macro_f1"] > best_f1:
            best_f1 = metrics["macro_f1"]
            best_name = name
            best_pipeline = pipeline

    train_dist = y_train.value_counts().to_dict()
    test_dist = y_test.value_counts().to_dict()

    metadata = {
        "scope": "semester_level",
        "dataset_type": "synthetic_prototype",
        "dataset_version": "2026-11-13",
        "synthetic_data_disclaimer": SYNTHETIC_DISCLAIMER,
        "training_timestamp": datetime.now(timezone.utc).isoformat(),
        "total_rows": len(df),
        "train_rows": len(X_train),
        "test_rows": len(X_test),
        "train_unique_students": int(len(set(g_train))),
        "test_unique_students": int(len(set(g_test))),
        "target_classes": classes,
        "feature_names": feature_cols,
        "numeric_features": numeric_cols,
        "categorical_features": categorical_cols,
        "train_class_distribution": train_dist,
        "test_class_distribution": test_dist,
        "selected_algorithm": best_name,
        "selected_macro_f1": best_f1,
        "evaluation_metrics": results[best_name],
        "all_models_comparison": {k: {m: v[m] for m in ["accuracy", "balanced_accuracy", "macro_f1"]} for k, v in results.items()},
        "train_test_split_method": "GroupShuffleSplit(student_id, test_size=0.2)",
        "random_seed": random_state,
    }

    if save_artifacts:
        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        model_path = ARTIFACTS_DIR / "semester_level_pipeline.joblib"
        meta_path = ARTIFACTS_DIR / "semester_level_metadata.json"

        joblib.dump(best_pipeline, model_path)
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

    return {
        "best_algorithm": best_name,
        "best_pipeline": best_pipeline,
        "results": results,
        "metadata": metadata,
    }


def train_all_mca_pipelines(random_state: int = 42) -> Dict[str, Any]:
    """Train, evaluate, and save artifacts for both subject and semester scopes."""
    subj = train_subject_level_pipelines(random_state=random_state, save_artifacts=True)
    sem = train_semester_level_pipelines(random_state=random_state, save_artifacts=True)
    return {
        "subject_level": subj,
        "semester_level": sem,
    }
