"""
backend/app/services/__init__.py

Exports service layer modules and helpers.
Uses lazy attribute loading for Phase 1 UCI prediction services to avoid
triggering external C-extension DLL policy blocks when importing MCA services.
"""

from app.services.mca_feature_extraction import (
    extract_academic_features,
    extract_subject_academic_features,
    extract_semester_academic_features,
    FeatureExtractionError,
    InvalidCutoffTimestampError,
    InvalidPredictionScopeError,
    EntityNotFoundError,
)
from app.services.mca_prediction_service import (
    persist_mca_prediction,
    get_mca_prediction_by_id,
    list_mca_predictions_by_student,
    list_mca_predictions_by_registration,
    PredictionPersistenceError,
    InvalidPredictionPayloadError,
)

_PHASE1_EXPORTS = {
    "load_model_artifact",
    "predict_and_recommend",
    "extract_weak_areas",
    "clear_model_cache",
}


def __getattr__(name: str):
    if name in _PHASE1_EXPORTS:
        import app.services.prediction_service as _ps
        return getattr(_ps, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "load_model_artifact",
    "predict_and_recommend",
    "extract_weak_areas",
    "clear_model_cache",
    "extract_academic_features",
    "extract_subject_academic_features",
    "extract_semester_academic_features",
    "FeatureExtractionError",
    "InvalidCutoffTimestampError",
    "InvalidPredictionScopeError",
    "EntityNotFoundError",
    "persist_mca_prediction",
    "get_mca_prediction_by_id",
    "list_mca_predictions_by_student",
    "list_mca_predictions_by_registration",
    "PredictionPersistenceError",
    "InvalidPredictionPayloadError",
]
