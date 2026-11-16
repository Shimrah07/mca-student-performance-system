"""
ML source modules: preprocessing, pipelines, model definitions, and MCA synthetic ML pipelines.
"""

# MCA Synthetic Dataset & Feature Adapter
from ml.src.mca_dataset_loader import (
    load_subject_level_dataset,
    load_semester_level_dataset,
    validate_dataset_schema,
)
from ml.src.mca_feature_adapter import (
    SUBJECT_LEVEL_AUDIT,
    SEMESTER_LEVEL_AUDIT,
    get_feature_compatibility_audit,
    adapt_phase2e_subject_payload,
    adapt_phase2e_semester_payload,
)

# MCA Training & Evaluation
from ml.src.mca_trainer import (
    split_dataset_by_student_group,
    build_preprocessor,
    evaluate_classifier,
    train_subject_level_pipelines,
    train_semester_level_pipelines,
    train_all_mca_pipelines,
)

# MCA Prediction Interface
from ml.src.mca_predictor import (
    predict_subject_performance,
    predict_semester_performance,
    batch_predict_subject_performance,
    batch_predict_semester_performance,
    get_model_metadata,
    load_subject_model,
    load_semester_model,
    clear_mca_model_cache,
)

__all__ = [
    # Dataset Loader
    "load_subject_level_dataset",
    "load_semester_level_dataset",
    "validate_dataset_schema",
    # Feature Adapter
    "SUBJECT_LEVEL_AUDIT",
    "SEMESTER_LEVEL_AUDIT",
    "get_feature_compatibility_audit",
    "adapt_phase2e_subject_payload",
    "adapt_phase2e_semester_payload",
    # Trainer
    "split_dataset_by_student_group",
    "build_preprocessor",
    "evaluate_classifier",
    "train_subject_level_pipelines",
    "train_semester_level_pipelines",
    "train_all_mca_pipelines",
    # Predictor
    "predict_subject_performance",
    "predict_semester_performance",
    "batch_predict_subject_performance",
    "batch_predict_semester_performance",
    "get_model_metadata",
    "load_subject_model",
    "load_semester_model",
    "clear_mca_model_cache",
]
