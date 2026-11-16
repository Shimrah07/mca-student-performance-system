"""
backend/app/services/prediction_service.py

Model serving service for the AI-Based Student Performance Prediction System.

Responsibilities:
- Safely loads and caches the 4 trained scikit-learn candidate pipelines and metadata.
- Validates model artifact availability and returns clear, non-sensitive errors if missing.
- Formats incoming student features into a 1-row DataFrame matching the exact feature order.
- Generates predictions and indicative (uncalibrated) class probabilities.
- Integrates with ml.src.recommendations to produce rule-based guidance.
- Purely serves inference: NEVER retrains models during request handling.
"""

import json
import logging
import sys
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import pandas as pd
from sklearn.pipeline import Pipeline

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.src.recommendations import generate_recommendations

logger = logging.getLogger(__name__)

# Map normalized (subject, scenario) tuples to artifact prefixes
ARTIFACT_MAP: Dict[Tuple[str, str], str] = {
    ("mathematics", "a"): "student_mat_scenario_a_logistic_regression",
    ("mathematics", "b"): "student_mat_scenario_b_decision_tree",
    ("portuguese", "a"): "student_por_scenario_a_random_forest",
    ("portuguese", "b"): "student_por_scenario_b_decision_tree",
}

# Cache for loaded (Pipeline, metadata_dict) indexed by artifact key
_MODEL_CACHE: Dict[str, Tuple[Pipeline, Dict[str, Any]]] = {}
_CACHE_LOCK = threading.Lock()


def get_models_directory() -> Path:
    """
    Locate the ml/models/ directory relative to project root.
    """
    # backend/app/services/prediction_service.py -> backend/app/services -> backend/app -> backend -> root
    root_dir = Path(__file__).resolve().parent.parent.parent.parent
    return root_dir / "ml" / "models"


def normalize_subject_scenario(subject: str, scenario: str) -> Tuple[str, str]:
    """
    Normalize subject and scenario strings for consistent lookup.
    Example: ('Mathematics', 'Scenario A') -> ('mathematics', 'a')
    """
    sub = subject.lower().strip()
    scen = scenario.lower().replace("scenario", "").strip()
    return sub, scen


def load_model_artifact(subject: str, scenario: str, models_dir: Optional[Path] = None) -> Tuple[Pipeline, Dict[str, Any]]:
    """
    Load and cache a candidate pipeline and its companion metadata JSON.

    Thread-safe and cached: loads each pipeline from disk only on first request.
    """
    norm_sub, norm_scen = normalize_subject_scenario(subject, scenario)
    cache_key = f"{norm_sub}_{norm_scen}"

    if cache_key in _MODEL_CACHE:
        return _MODEL_CACHE[cache_key]

    with _CACHE_LOCK:
        # Double-check inside lock
        if cache_key in _MODEL_CACHE:
            return _MODEL_CACHE[cache_key]

        if (norm_sub, norm_scen) not in ARTIFACT_MAP:
            raise ValueError(
                f"Unsupported subject/scenario combination: subject='{subject}', scenario='{scenario}'. "
                f"Supported subjects: ['Mathematics', 'Portuguese'], scenarios: ['Scenario A', 'Scenario B']."
            )

        artifact_prefix = ARTIFACT_MAP[(norm_sub, norm_scen)]
        target_dir = models_dir or get_models_directory()
        joblib_path = target_dir / f"{artifact_prefix}.joblib"
        json_path = target_dir / f"{artifact_prefix}.json"

        if not joblib_path.exists():
            raise FileNotFoundError(
                f"Candidate model artifact '{joblib_path.name}' not found. "
                f"Please ensure offline training persistence has generated models under ml/models/."
            )
        if not json_path.exists():
            raise FileNotFoundError(
                f"Companion metadata artifact '{json_path.name}' not found."
            )

        try:
            pipeline = joblib.load(joblib_path)
            with open(json_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
        except Exception as exc:
            logger.error("Failed to load model artifact %s: %s", artifact_prefix, exc)
            raise RuntimeError(f"Error loading model artifact '{artifact_prefix}': {exc}") from exc

        _MODEL_CACHE[cache_key] = (pipeline, metadata)
        logger.info("Successfully loaded and cached pipeline: %s", artifact_prefix)
        return pipeline, metadata


def clear_model_cache() -> None:
    """Clear cached pipelines (primarily used in testing)."""
    with _CACHE_LOCK:
        _MODEL_CACHE.clear()


def extract_weak_areas(input_dict: Dict[str, Any], predicted_category: str) -> List[str]:
    """
    Identify factor-level academic risk indicators based on student inputs.
    """
    weak_areas: List[str] = []

    # Study time risk
    studytime = input_dict.get("studytime")
    if studytime is not None and int(studytime) <= 2 and predicted_category in ("Needs Improvement", "Average"):
        weak_areas.append("Low weekly study time (<= 5 hours)")

    # Absences risk
    absences = input_dict.get("absences")
    if absences is not None and int(absences) >= 5:
        weak_areas.append(f"High absenteeism ({absences} absences)")

    # Prior failures risk
    failures = input_dict.get("failures")
    if failures is not None and int(failures) > 0:
        weak_areas.append(f"Previous subject failure ({failures} record(s))")

    # Early assessment risk (Scenario B)
    g1 = input_dict.get("G1")
    if g1 is not None and float(g1) < 10:
        weak_areas.append(f"Below-passing first-period grade ({g1}/20)")

    return weak_areas


def predict_and_recommend(
    subject: str,
    scenario: str,
    features_dict: Dict[str, Any],
    models_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Execute full inference and recommendation workflow for a student:
    1. Retrieve cached pipeline & metadata.
    2. Format input features into a 1-row DataFrame.
    3. Predict performance category and indicative probabilities.
    4. Generate supportive rule-based recommendations.
    5. Return complete structured response dictionary.
    """
    pipeline, metadata = load_model_artifact(subject, scenario, models_dir=models_dir)

    # Filter features strictly to the model's expected inputs (guarantees G2 and G3 are never passed)
    expected_features: List[str] = metadata["feature_names"]
    input_row = {col: features_dict.get(col) for col in expected_features}

    # Verify no required features are missing
    missing_cols = [col for col in expected_features if input_row[col] is None]
    if missing_cols:
        raise ValueError(f"Missing required feature(s) for {scenario}: {missing_cols}")

    # Build DataFrame matching feature ordering
    df_input = pd.DataFrame([input_row])[expected_features]

    # Predict class
    predicted_category = str(pipeline.predict(df_input)[0])

    # Predict probabilities (if supported by pipeline)
    probabilities: Optional[Dict[str, float]] = None
    if hasattr(pipeline, "predict_proba"):
        prob_arr = pipeline.predict_proba(df_input)[0]
        classes = pipeline.classes_
        probabilities = {str(cls): round(float(p), 4) for cls, p in zip(classes, prob_arr)}

    # Generate rule-based recommendations
    recommendations_payload = generate_recommendations(
        student_data=features_dict,
        predicted_category=predicted_category,
    )

    # Extract weak areas
    weak_areas = extract_weak_areas(features_dict, predicted_category)

    return {
        "predicted_category": predicted_category,
        "subject": metadata["subject"],
        "scenario": f"Scenario {metadata['scenario']}",
        "model_name": metadata["model_name"],
        "model_version": metadata.get("model_version", "1.0.0"),
        "prediction_probabilities": probabilities,
        "summary": recommendations_payload["summary"],
        "actionable_recommendations": recommendations_payload["actionable_recommendations"],
        "strengths_identified": recommendations_payload["strengths_identified"],
        "evaluated_factors": recommendations_payload["evaluated_factors"],
        "disclaimer": recommendations_payload["disclaimer"],
        "weak_areas": weak_areas,
        "clean_input_snapshot": input_row,
    }
