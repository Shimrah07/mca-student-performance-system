"""
ml/src/train_models.py

Baseline model training, cross-validation, and test evaluation for the
AI-Based Student Performance Prediction System.

Enforces project methodology:
- Reuses preprocessing from ml.src.preprocessing (no duplicated logic).
- Strict leakage prevention: preprocessor and model are chained in a Pipeline
  and fitted independently within each cross-validation fold.
- Evaluates Logistic Regression, Decision Tree, and Random Forest.
- Primary comparison metric: Macro F1-score.
- Conducts separate experiments for Mathematics and Portuguese across Scenarios A & B.
"""

import json
import joblib
from pathlib import Path
from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np

from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    classification_report,
    confusion_matrix,
)

from ml.src.preprocessing import (
    load_raw_dataset,
    prepare_features_and_target,
    split_data,
    build_preprocessor,
    PERFORMANCE_CATEGORIES,
)


def get_baseline_models(random_state: int = 42) -> Dict[str, Any]:
    """
    Return candidate baseline multi-class classifiers.

    Includes both balanced and unweighted variants to document the impact
    of class weighting on our imbalanced student performance categories.
    """
    return {
        "Logistic Regression (balanced)": LogisticRegression(
            max_iter=1000,
            random_state=random_state,
            class_weight="balanced",
        ),
        "Logistic Regression (unweighted)": LogisticRegression(
            max_iter=1000,
            random_state=random_state,
        ),
        "Decision Tree (balanced)": DecisionTreeClassifier(
            max_depth=5,
            random_state=random_state,
            class_weight="balanced",
        ),
        "Decision Tree (unweighted)": DecisionTreeClassifier(
            max_depth=5,
            random_state=random_state,
        ),
        "Random Forest (balanced)": RandomForestClassifier(
            n_estimators=100,
            max_depth=6,
            random_state=random_state,
            class_weight="balanced",
        ),
        "Random Forest (unweighted)": RandomForestClassifier(
            n_estimators=100,
            max_depth=6,
            random_state=random_state,
        ),
    }


def build_full_pipeline(scenario: str, classifier: Any) -> Pipeline:
    """
    Construct a complete end-to-end Pipeline combining the ColumnTransformer
    preprocessor with a target classifier.
    """
    preprocessor = build_preprocessor(scenario=scenario)
    return Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("classifier", classifier),
    ])


def run_cross_validation(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    scenario: str,
    models: Dict[str, Any],
    cv_splits: int = 5,
    random_state: int = 42,
) -> pd.DataFrame:
    """
    Perform Stratified K-Fold Cross-Validation on the training set.

    Guarantees no data leakage: the entire pipeline (including OneHotEncoder
    and StandardScaler) is fitted independently on the training folds of each split.
    """
    cv = StratifiedKFold(n_splits=cv_splits, shuffle=True, random_state=random_state)
    records = []

    for name, model in models.items():
        pipeline = build_full_pipeline(scenario=scenario, classifier=model)

        scores = cross_validate(
            pipeline,
            X_train,
            y_train,
            cv=cv,
            scoring=["f1_macro", "accuracy", "f1_weighted"],
            n_jobs=-1,
        )

        records.append({
            "model_name": name,
            "macro_f1_mean": float(np.mean(scores["test_f1_macro"])),
            "macro_f1_std": float(np.std(scores["test_f1_macro"])),
            "accuracy_mean": float(np.mean(scores["test_accuracy"])),
            "accuracy_std": float(np.std(scores["test_accuracy"])),
            "weighted_f1_mean": float(np.mean(scores["test_f1_weighted"])),
            "raw_pipeline": pipeline,
        })

    results_df = pd.DataFrame(records).sort_values(
        by="macro_f1_mean", ascending=False
    ).reset_index(drop=True)

    return results_df


def evaluate_model_on_test(
    pipeline: Pipeline,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> Dict[str, Any]:
    """
    Fit the chosen pipeline on the entire training set, then evaluate on the
    held-out test set (unseen 20%).

    Returns a dictionary of comprehensive test metrics, confusion matrix,
    and per-class classification report.
    """
    # Fit pipeline strictly on full training set
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)

    acc = float(accuracy_score(y_test, y_pred))
    macro_f1 = float(f1_score(y_test, y_pred, average="macro", labels=PERFORMANCE_CATEGORIES))
    weighted_f1 = float(f1_score(y_test, y_pred, average="weighted", labels=PERFORMANCE_CATEGORIES))

    report_dict = classification_report(
        y_test,
        y_pred,
        labels=PERFORMANCE_CATEGORIES,
        output_dict=True,
        zero_division=0,
    )
    report_text = classification_report(
        y_test,
        y_pred,
        labels=PERFORMANCE_CATEGORIES,
        digits=4,
        zero_division=0,
    )

    cm = confusion_matrix(y_test, y_pred, labels=PERFORMANCE_CATEGORIES)
    cm_df = pd.DataFrame(
        cm,
        index=[f"True: {c}" for c in PERFORMANCE_CATEGORIES],
        columns=[f"Pred: {c}" for c in PERFORMANCE_CATEGORIES],
    )

    return {
        "fitted_pipeline": pipeline,
        "test_accuracy": acc,
        "test_macro_f1": macro_f1,
        "test_weighted_f1": weighted_f1,
        "classification_report_dict": report_dict,
        "classification_report_text": report_text,
        "confusion_matrix_df": cm_df,
    }


def run_experiment(
    csv_path: str | Path,
    scenario: str,
    random_state: int = 42,
) -> Dict[str, Any]:
    """
    Execute a complete training and evaluation experiment for a given CSV
    dataset and scenario.
    """
    df = load_raw_dataset(csv_path)
    X, y = prepare_features_and_target(df, scenario=scenario)
    X_train, X_test, y_train, y_test = split_data(
        X, y, test_size=0.20, random_state=random_state
    )

    models = get_baseline_models(random_state=random_state)
    cv_results = run_cross_validation(
        X_train, y_train, scenario=scenario, models=models, random_state=random_state
    )

    # Select candidate with highest Macro F1 in cross-validation
    best_candidate_name = cv_results.iloc[0]["model_name"]
    best_pipeline = cv_results.iloc[0]["raw_pipeline"]

    test_eval = evaluate_model_on_test(
        best_pipeline, X_train, y_train, X_test, y_test
    )

    return {
        "scenario": scenario,
        "X_train_shape": X_train.shape,
        "X_test_shape": X_test.shape,
        "cv_results_df": cv_results.drop(columns=["raw_pipeline"]),
        "best_candidate_name": best_candidate_name,
        "best_cv_macro_f1": cv_results.iloc[0]["macro_f1_mean"],
        "test_evaluation": test_eval,
    }


# ---------------------------------------------------------------------------
# Stage 2, Step 4: Approved Candidate Configurations & Persistence Workflow
# ---------------------------------------------------------------------------

SELECTED_CANDIDATE_CONFIGS = {
    ("Mathematics", "A"): {
        "artifact_prefix": "student_mat_scenario_a_logistic_regression",
        "subject": "Mathematics",
        "scenario": "A",
        "csv_filename": "student-mat.csv",
        "model_name": "Logistic Regression (unweighted)",
        "classifier_class": "LogisticRegression",
        "class_weight": None,
        "instantiate_classifier": lambda rs: LogisticRegression(max_iter=1000, random_state=rs),
    },
    ("Mathematics", "B"): {
        "artifact_prefix": "student_mat_scenario_b_decision_tree",
        "subject": "Mathematics",
        "scenario": "B",
        "csv_filename": "student-mat.csv",
        "model_name": "Decision Tree (unweighted)",
        "classifier_class": "DecisionTreeClassifier",
        "class_weight": None,
        "instantiate_classifier": lambda rs: DecisionTreeClassifier(max_depth=5, random_state=rs),
    },
    ("Portuguese", "A"): {
        "artifact_prefix": "student_por_scenario_a_random_forest",
        "subject": "Portuguese",
        "scenario": "A",
        "csv_filename": "student-por.csv",
        "model_name": "Random Forest (balanced)",
        "classifier_class": "RandomForestClassifier",
        "class_weight": "balanced",
        "instantiate_classifier": lambda rs: RandomForestClassifier(
            n_estimators=100, max_depth=6, random_state=rs, class_weight="balanced"
        ),
    },
    ("Portuguese", "B"): {
        "artifact_prefix": "student_por_scenario_b_decision_tree",
        "subject": "Portuguese",
        "scenario": "B",
        "csv_filename": "student-por.csv",
        "model_name": "Decision Tree (balanced)",
        "classifier_class": "DecisionTreeClassifier",
        "class_weight": "balanced",
        "instantiate_classifier": lambda rs: DecisionTreeClassifier(
            max_depth=5, random_state=rs, class_weight="balanced"
        ),
    },
}


def persist_candidate_models(
    models_dir: str | Path,
    data_dir: str | Path,
    random_state: int = 42,
) -> Dict[str, Any]:
    """
    Train, evaluate, and persist the four approved candidate models.

    Methodology:
    1. Independent validation:
       - Evaluates Stratified 5-Fold Cross-Validation on the 80% train split.
       - Evaluates generalization on the held-out 20% test split.
       - Records all validation metrics and confusion matrices.
    2. Production refit:
       - Fits an independent persistence pipeline on the 100% full dataset
         so the production model benefits from all verified records.
       - Clearly separates the full-data refit artifact from the held-out
         evaluation metrics in the saved JSON metadata.
    3. Artifact storage:
       - Saves complete Pipeline as .joblib file.
       - Saves companion .json metadata documenting dataset, features, cutoffs,
         evaluation metrics, and calibration status.
    """
    models_path = Path(models_dir)
    data_path = Path(data_dir)
    models_path.mkdir(parents=True, exist_ok=True)

    summary_records = {}

    for (subject, scenario), cfg in SELECTED_CANDIDATE_CONFIGS.items():
        csv_file = data_path / cfg["csv_filename"]
        df = load_raw_dataset(csv_file)
        X, y = prepare_features_and_target(df, scenario=scenario)

        # 1. 80/20 train/test split for independent metrics reporting
        X_train, X_test, y_train, y_test = split_data(
            X, y, test_size=0.20, random_state=random_state
        )

        eval_model = cfg["instantiate_classifier"](random_state)
        eval_pipeline = build_full_pipeline(scenario=scenario, classifier=eval_model)

        # Cross-validation on 80% train partition
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=random_state)
        cv_scores = cross_validate(
            eval_pipeline,
            X_train,
            y_train,
            cv=cv,
            scoring=["f1_macro", "accuracy", "f1_weighted"],
            n_jobs=-1,
        )

        cv_metrics = {
            "macro_f1_mean": float(np.mean(cv_scores["test_f1_macro"])),
            "macro_f1_std": float(np.std(cv_scores["test_f1_macro"])),
            "accuracy_mean": float(np.mean(cv_scores["test_accuracy"])),
            "accuracy_std": float(np.std(cv_scores["test_accuracy"])),
            "weighted_f1_mean": float(np.mean(cv_scores["test_f1_weighted"])),
        }

        # Held-out 20% test evaluation
        test_eval = evaluate_model_on_test(
            eval_pipeline, X_train, y_train, X_test, y_test
        )

        # 2. Production artifact: Refit on 100% full dataset
        prod_model = cfg["instantiate_classifier"](random_state)
        prod_pipeline = build_full_pipeline(scenario=scenario, classifier=prod_model)
        prod_pipeline.fit(X, y)

        # 3. Save joblib pipeline
        joblib_filename = f"{cfg['artifact_prefix']}.joblib"
        joblib_path = models_path / joblib_filename
        joblib.dump(prod_pipeline, joblib_path)

        # 4. Save companion metadata JSON
        metadata = {
            "artifact_filename": joblib_filename,
            "subject": subject,
            "scenario": scenario,
            "scenario_description": (
                "Early-Warning model excluding G1, G2, and G3"
                if scenario == "A"
                else "Mid-Term model including G1 but excluding G2 and G3"
            ),
            "model_name": cfg["model_name"],
            "classifier_class": cfg["classifier_class"],
            "class_weight_setting": cfg["class_weight"],
            "dataset_source": "UCI Machine Learning Repository - Student Performance (Cortez & Silva, 2008)",
            "dataset_file": cfg["csv_filename"],
            "total_records": int(len(df)),
            "feature_count": int(X.shape[1]),
            "feature_names": list(X.columns),
            "excluded_features": ["G1", "G2", "G3"] if scenario == "A" else ["G2", "G3"],
            "target_name": "performance_category",
            "target_classes": PERFORMANCE_CATEGORIES,
            "category_mapping": {
                "Needs Improvement": "G3 in [0, 9] (Below Portuguese pass threshold 10)",
                "Average": "G3 in [10, 13] (Sufficient passing marks)",
                "Good": "G3 in [14, 15] (Good standing)",
                "Excellent": "G3 in [16, 20] (Distinction)",
            },
            "random_seed": random_state,
            "training_and_evaluation_methodology": (
                "Cross-validation (5-fold stratified) conducted on 80% train split. "
                "Generalization evaluated on unseen 20% held-out test split. "
                "Final persistence pipeline refitted on 100% full dataset."
            ),
            "cross_validation_metrics": {
                "macro_f1_mean": round(cv_metrics["macro_f1_mean"], 4),
                "macro_f1_std": round(cv_metrics["macro_f1_std"], 4),
                "accuracy_mean": round(cv_metrics["accuracy_mean"], 4),
                "accuracy_std": round(cv_metrics["accuracy_std"], 4),
                "weighted_f1_mean": round(cv_metrics["weighted_f1_mean"], 4),
            },
            "held_out_test_metrics": {
                "test_accuracy": round(test_eval["test_accuracy"], 4),
                "test_macro_f1": round(test_eval["test_macro_f1"], 4),
                "test_weighted_f1": round(test_eval["test_weighted_f1"], 4),
                "per_class": test_eval["classification_report_dict"],
            },
            "persistence_scope": "Full dataset refit (100% data). Note: Held-out test metrics reflect earlier 80/20 evaluation, not a new test score on the refitted model.",
            "calibration_status": "Uncalibrated probabilities (deferred to future stage as prototype focuses on category prediction and ranking)",
        }

        json_filename = f"{cfg['artifact_prefix']}.json"
        json_path = models_path / json_filename
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        summary_records[f"{subject}_{scenario}"] = {
            "joblib_path": str(joblib_path),
            "json_path": str(json_path),
            "cv_macro_f1": cv_metrics["macro_f1_mean"],
            "test_macro_f1": test_eval["test_macro_f1"],
            "test_accuracy": test_eval["test_accuracy"],
            "test_confusion_matrix": test_eval["confusion_matrix_df"],
            "test_classification_report": test_eval["classification_report_text"],
        }

    return summary_records


def load_persisted_model(artifact_path: str | Path) -> Pipeline:
    """
    Load a serialized scikit-learn Pipeline from a .joblib file.
    """
    path = Path(artifact_path)
    if not path.is_file():
        raise FileNotFoundError(f"Model artifact not found: {path.resolve()}")
    return joblib.load(path)

