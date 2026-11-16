"""
ml/src/mca_predictor.py

Reusable prediction interface for MCA Performance Tier Machine Learning models.
Accepts raw feature dictionaries or Phase 2E academic feature extraction payloads,
validates schema compatibility, formats input vectors, runs inference against
trained pipelines, and returns standardized predictions with probabilities,
confidence scores, audit metadata, and synthetic data warnings.
"""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import ml.src.mca_compat  # Ensure sklearn C-extension stubs if restricted by OS

import joblib
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline

from ml.src.mca_feature_adapter import (
    SEMESTER_LEVEL_AUDIT,
    SUBJECT_LEVEL_AUDIT,
    adapt_phase2e_semester_payload,
    adapt_phase2e_subject_payload,
)

DEFAULT_ARTIFACTS_DIR = Path("ml/artifacts/mca")

def _resolve_artifacts_dir(override_dir: Optional[Union[str, Path]] = None) -> Path:
    """Resolve artifacts directory relative to current working directory or ml/ root."""
    if override_dir:
        p = Path(override_dir)
        if p.exists() and p.is_dir():
            return p
        return p

    candidates = [
        DEFAULT_ARTIFACTS_DIR,
        Path(__file__).resolve().parent.parent / "artifacts" / "mca",
        Path("backend/ml/artifacts/mca"),
    ]
    for c in candidates:
        if c.exists() and c.is_dir():
            return c

    # Fallback to absolute repository path
    return Path(__file__).resolve().parent.parent / "artifacts" / "mca"

SYNTHETIC_WARNING = (
    "WARNING: This prediction was produced by a prototype model trained exclusively "
    "on synthetic data (Phase 3A). It must NOT be used for actual academic decisions, "
    "grading evaluations, or official student assessments."
)

# In-memory artifact caches
_SUBJECT_PIPELINE: Optional[Pipeline] = None
_SUBJECT_METADATA: Optional[Dict[str, Any]] = None
_SEMESTER_PIPELINE: Optional[Pipeline] = None
_SEMESTER_METADATA: Optional[Dict[str, Any]] = None


def clear_mca_model_cache() -> None:
    """Clear in-memory cached model pipelines and metadata."""
    global _SUBJECT_PIPELINE, _SUBJECT_METADATA, _SEMESTER_PIPELINE, _SEMESTER_METADATA
    _SUBJECT_PIPELINE = None
    _SUBJECT_METADATA = None
    _SEMESTER_PIPELINE = None
    _SEMESTER_METADATA = None


# ===========================================================================
# Artifact Loading Helpers
# ===========================================================================

def load_subject_model(
    artifacts_dir: Optional[Union[str, Path]] = None,
    force_reload: bool = False,
) -> Tuple[Pipeline, Dict[str, Any]]:
    """Load and cache the trained subject-level pipeline and metadata."""
    global _SUBJECT_PIPELINE, _SUBJECT_METADATA

    if _SUBJECT_PIPELINE is not None and _SUBJECT_METADATA is not None and not force_reload:
        return _SUBJECT_PIPELINE, _SUBJECT_METADATA

    base_dir = _resolve_artifacts_dir(artifacts_dir)
    model_path = base_dir / "subject_level_pipeline.joblib"
    meta_path = base_dir / "subject_level_metadata.json"

    if not model_path.exists():
        raise FileNotFoundError(
            f"Subject-level model artifact not found at '{model_path}'. "
            "Please run train_subject_level_pipelines() first."
        )
    if not meta_path.exists():
        raise FileNotFoundError(
            f"Subject-level metadata not found at '{meta_path}'. "
            "Please run train_subject_level_pipelines() first."
        )

    pipeline = joblib.load(model_path)
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    if not force_reload:
        _SUBJECT_PIPELINE = pipeline
        _SUBJECT_METADATA = meta

    return pipeline, meta


def load_semester_model(
    artifacts_dir: Optional[Union[str, Path]] = None,
    force_reload: bool = False,
) -> Tuple[Pipeline, Dict[str, Any]]:
    """Load and cache the trained semester-level pipeline and metadata."""
    global _SEMESTER_PIPELINE, _SEMESTER_METADATA

    if _SEMESTER_PIPELINE is not None and _SEMESTER_METADATA is not None and not force_reload:
        return _SEMESTER_PIPELINE, _SEMESTER_METADATA

    base_dir = _resolve_artifacts_dir(artifacts_dir)
    model_path = base_dir / "semester_level_pipeline.joblib"
    meta_path = base_dir / "semester_level_metadata.json"

    if not model_path.exists():
        raise FileNotFoundError(
            f"Semester-level model artifact not found at '{model_path}'. "
            "Please run train_semester_level_pipelines() first."
        )
    if not meta_path.exists():
        raise FileNotFoundError(
            f"Semester-level metadata not found at '{meta_path}'. "
            "Please run train_semester_level_pipelines() first."
        )

    pipeline = joblib.load(model_path)
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    if not force_reload:
        _SEMESTER_PIPELINE = pipeline
        _SEMESTER_METADATA = meta

    return pipeline, meta


def get_model_metadata(
    scope: str = "subject_level",
    artifacts_dir: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """Retrieve metadata for a specified model scope."""
    if scope == "subject_level":
        _, meta = load_subject_model(artifacts_dir)
        return meta
    elif scope == "semester_level":
        _, meta = load_semester_model(artifacts_dir)
        return meta
    else:
        raise ValueError(f"Unknown scope: {scope}. Must be 'subject_level' or 'semester_level'.")


# ===========================================================================
# Input Normalization & Compatibility Auditing
# ===========================================================================

def _normalize_subject_input(payload: Union[Dict[str, Any], pd.DataFrame]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Convert raw input or Phase 2E extraction dict to DataFrame and audit compatibility."""
    if isinstance(payload, pd.DataFrame):
        df = payload.copy()
        used = [c for c in SUBJECT_LEVEL_AUDIT["supported_features"] if c in df.columns]
        missing = [c for c in SUBJECT_LEVEL_AUDIT["supported_features"] if c not in df.columns]
        ignored = [c for c in df.columns if c not in SUBJECT_LEVEL_AUDIT["supported_features"]]
        for col in missing:
            df[col] = np.nan
        df = df[SUBJECT_LEVEL_AUDIT["supported_features"]]
        return df, {"used_features": used, "missing_features": missing, "ignored_features": ignored}

    if not isinstance(payload, dict):
        raise TypeError(f"Payload must be a dict or pd.DataFrame, got {type(payload).__name__}")

    if not payload:
        raise ValueError("Payload cannot be empty.")

    # Check if Phase 2E extraction format
    if "features" in payload or "metadata" in payload:
        df = adapt_phase2e_subject_payload(payload)
        features_dict = payload.get("features", {})
        used = [k for k in features_dict.keys() if features_dict[k] is not None]
        missing = [k for k in features_dict.keys() if features_dict[k] is None]
        return df, {
            "payload_format": "phase_2e_extraction",
            "used_features": SUBJECT_LEVEL_AUDIT["supported_features"],
            "missing_features": missing,
            "ignored_features": [k for k in payload.keys() if k not in ("features", "metadata")],
        }

    # Raw dictionary input
    used = [c for c in SUBJECT_LEVEL_AUDIT["supported_features"] if c in payload]
    missing = [c for c in SUBJECT_LEVEL_AUDIT["supported_features"] if c not in payload]
    ignored = [c for c in payload.keys() if c not in SUBJECT_LEVEL_AUDIT["supported_features"]]

    row = {c: payload.get(c, np.nan) for c in SUBJECT_LEVEL_AUDIT["supported_features"]}
    df = pd.DataFrame([row])[SUBJECT_LEVEL_AUDIT["supported_features"]]
    return df, {"payload_format": "raw_dict", "used_features": used, "missing_features": missing, "ignored_features": ignored}


def _normalize_semester_input(payload: Union[Dict[str, Any], pd.DataFrame]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Convert raw input or Phase 2E extraction dict to DataFrame and audit compatibility."""
    if isinstance(payload, pd.DataFrame):
        df = payload.copy()
        used = [c for c in SEMESTER_LEVEL_AUDIT["supported_features"] if c in df.columns]
        missing = [c for c in SEMESTER_LEVEL_AUDIT["supported_features"] if c not in df.columns]
        ignored = [c for c in df.columns if c not in SEMESTER_LEVEL_AUDIT["supported_features"]]
        for col in missing:
            df[col] = np.nan
        df = df[SEMESTER_LEVEL_AUDIT["supported_features"]]
        return df, {"used_features": used, "missing_features": missing, "ignored_features": ignored}

    if not isinstance(payload, dict):
        raise TypeError(f"Payload must be a dict or pd.DataFrame, got {type(payload).__name__}")

    if not payload:
        raise ValueError("Payload cannot be empty.")

    # Check if Phase 2E extraction format
    if "features" in payload or "metadata" in payload:
        df = adapt_phase2e_semester_payload(payload)
        features_dict = payload.get("features", {})
        used = [k for k in features_dict.keys() if features_dict[k] is not None]
        missing = [k for k in features_dict.keys() if features_dict[k] is None]
        return df, {
            "payload_format": "phase_2e_extraction",
            "used_features": SEMESTER_LEVEL_AUDIT["supported_features"],
            "missing_features": missing,
            "ignored_features": [k for k in payload.keys() if k not in ("features", "metadata")],
        }

    # Raw dictionary input
    used = [c for c in SEMESTER_LEVEL_AUDIT["supported_features"] if c in payload]
    missing = [c for c in SEMESTER_LEVEL_AUDIT["supported_features"] if c not in payload]
    ignored = [c for c in payload.keys() if c not in SEMESTER_LEVEL_AUDIT["supported_features"]]

    row = {c: payload.get(c, np.nan) for c in SEMESTER_LEVEL_AUDIT["supported_features"]}
    df = pd.DataFrame([row])[SEMESTER_LEVEL_AUDIT["supported_features"]]
    return df, {"payload_format": "raw_dict", "used_features": used, "missing_features": missing, "ignored_features": ignored}


# ===========================================================================
# Prediction Interfaces
# ===========================================================================

def predict_subject_performance(
    features_payload: Union[Dict[str, Any], pd.DataFrame],
    artifacts_dir: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """
    Predict MCA subject-level performance tier from a feature payload.

    Args:
        features_payload: Dict from Phase 2E feature extraction, raw feature dict, or DataFrame.
        artifacts_dir: Optional custom path to model artifacts directory.

    Returns:
        Standardized prediction dictionary.
    """
    pipeline, meta = load_subject_model(artifacts_dir)
    df, audit = _normalize_subject_input(features_payload)

    predicted_tier = str(pipeline.predict(df)[0])

    # Extract probabilities if model supports predict_proba
    probs_dict = {}
    confidence = 1.0
    if hasattr(pipeline, "predict_proba"):
        probs = pipeline.predict_proba(df)[0]
        classes = pipeline.classes_
        probs_dict = {str(cls): round(float(p), 4) for cls, p in zip(classes, probs)}
        confidence = round(float(np.max(probs)), 4)

    return {
        "scope": "subject_level",
        "predicted_tier": predicted_tier,
        "confidence": confidence,
        "probabilities": probs_dict,
        "model_metadata": {
            "algorithm": meta.get("selected_algorithm"),
            "macro_f1": meta.get("selected_macro_f1"),
            "training_timestamp": meta.get("training_timestamp"),
            "dataset_type": meta.get("dataset_type"),
            "is_synthetic": True,
        },
        "compatibility_status": audit,
        "synthetic_data_warning": SYNTHETIC_WARNING,
        "prediction_timestamp": datetime.now(timezone.utc).isoformat(),
    }


def predict_semester_performance(
    features_payload: Union[Dict[str, Any], pd.DataFrame],
    artifacts_dir: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """
    Predict MCA semester-level performance tier from a feature payload.

    Args:
        features_payload: Dict from Phase 2E feature extraction, raw feature dict, or DataFrame.
        artifacts_dir: Optional custom path to model artifacts directory.

    Returns:
        Standardized prediction dictionary.
    """
    pipeline, meta = load_semester_model(artifacts_dir)
    df, audit = _normalize_semester_input(features_payload)

    predicted_tier = str(pipeline.predict(df)[0])

    probs_dict = {}
    confidence = 1.0
    if hasattr(pipeline, "predict_proba"):
        probs = pipeline.predict_proba(df)[0]
        classes = pipeline.classes_
        probs_dict = {str(cls): round(float(p), 4) for cls, p in zip(classes, probs)}
        confidence = round(float(np.max(probs)), 4)

    return {
        "scope": "semester_level",
        "predicted_tier": predicted_tier,
        "confidence": confidence,
        "probabilities": probs_dict,
        "model_metadata": {
            "algorithm": meta.get("selected_algorithm"),
            "macro_f1": meta.get("selected_macro_f1"),
            "training_timestamp": meta.get("training_timestamp"),
            "dataset_type": meta.get("dataset_type"),
            "is_synthetic": True,
        },
        "compatibility_status": audit,
        "synthetic_data_warning": SYNTHETIC_WARNING,
        "prediction_timestamp": datetime.now(timezone.utc).isoformat(),
    }


def batch_predict_subject_performance(
    payloads: List[Dict[str, Any]],
    artifacts_dir: Optional[Union[str, Path]] = None,
) -> List[Dict[str, Any]]:
    """Run subject-level predictions on a list of payloads."""
    return [predict_subject_performance(p, artifacts_dir=artifacts_dir) for p in payloads]


def batch_predict_semester_performance(
    payloads: List[Dict[str, Any]],
    artifacts_dir: Optional[Union[str, Path]] = None,
) -> List[Dict[str, Any]]:
    """Run semester-level predictions on a list of payloads."""
    return [predict_semester_performance(p, artifacts_dir=artifacts_dir) for p in payloads]
