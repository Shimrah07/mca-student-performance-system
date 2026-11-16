"""
ml/src/mca_feature_adapter.py

MCA Feature Compatibility Audit and Adapter Module.
Bridges Phase 2E point-in-time feature extraction schemas with machine learning
model training and inference pipelines.

Classifies all dataset columns into:
1. Supported by Phase 2E point-in-time extraction service.
2. Synthetic-only features (in prototype dataset but not in approved 13-table ORM).
3. Target outcome columns (strictly excluded to prevent data leakage).
4. Identifier and metadata columns (strictly excluded from model inputs).
"""

from typing import Any, Dict, List, Optional, Tuple
import pandas as pd


# ===========================================================================
# Feature Classification & Compatibility Audit Definitions
# ===========================================================================

SUBJECT_LEVEL_AUDIT = {
    # 1. Features supported by Phase 2E feature extraction service
    "supported_features": [
        "semester_number",
        "course_type",
        "attendance_percentage",
        "mst1_marks",
        "mst2_marks",
        "assignment_marks",              # Maps from Phase 2E 'assignment_score'
        "prior_sgpa",                    # Maps from Phase 2E 'latest_prior_sgpa'
        "prior_cgpa",                    # Maps from Phase 2E 'latest_declared_cgpa'
        "viva_marks",                    # Maps from Phase 2E 'viva_marks'
        "lab_journal_marks",             # Maps from Phase 2E 'lab_record_score'
        "synopsis_approved",             # Maps from Phase 2E 'synopsis_approved'
        "design_approved",               # Maps from Phase 2E 'design_score'
        "implementation_percentage",     # Maps from Phase 2E 'implementation_pct'
        "faculty_guide_interaction_score"# Maps from Phase 2E 'supervisor_score'
    ],
    # 2. Features in synthetic CSV but NOT in Phase 2B 13-table ORM schema
    "synthetic_only_features": [
        "study_hours_per_week",
        "math_background_score",
        "literature_survey_completed",
        "practical_attendance_percentage",
        "experiments_completed",
        "experiments_total",
    ],
    # 3. Target outcome columns (LEAKAGE RISK - NEVER MODEL INPUTS)
    "target_outcome_columns": [
        "synthetic_final_score",
        "performance_tier",
    ],
    # 4. Identifier / metadata columns (EXCLUDE FROM MODEL INPUTS)
    "identifier_metadata_columns": [
        "record_id",
        "student_id",
        "registration_id",
        "course_code",
        "course_title",
        "prediction_scope",
        "cutoff_timestamp",
        "data_origin",
    ],
}

SEMESTER_LEVEL_AUDIT = {
    # 1. Features supported by Phase 2E feature extraction service
    "supported_features": [
        "semester_number",
        "courses_included",              # Maps from Phase 2E 'total_enrolled_courses'
        "mean_attendance_percentage",    # Maps from Phase 2E 'average_attendance_percentage'
        "mean_mst1_marks",               # Maps from Phase 2E 'average_mst1_marks'
        "mean_mst2_marks",               # Maps from Phase 2E 'average_mst2_marks'
        "mean_assignment_marks",          # Maps from Phase 2E 'average_assignment_score'
        "mean_prior_sgpa",               # Maps from Phase 2E 'latest_prior_sgpa'
        "mean_prior_cgpa",               # Maps from Phase 2E 'latest_declared_cgpa'
    ],
    # 2. Features in synthetic CSV but NOT in Phase 2B 13-table ORM schema
    "synthetic_only_features": [
        "course_types_included",
        "mean_study_hours_per_week",
        "mean_math_background_score",
        "mean_practical_attendance_percentage",
        "mean_experiments_completed",
        "mean_experiments_total",
        "mean_viva_marks",
        "mean_lab_journal_marks",
        "mean_synopsis_approved",
        "mean_literature_survey_completed",
        "mean_design_approved",
        "mean_implementation_percentage",
        "mean_faculty_guide_interaction_score",
    ],
    # 3. Target outcome columns (LEAKAGE RISK - NEVER MODEL INPUTS)
    "target_outcome_columns": [
        "synthetic_semester_final_score",
        "performance_tier",
    ],
    # 4. Identifier / metadata columns (EXCLUDE FROM MODEL INPUTS)
    "identifier_metadata_columns": [
        "record_id",
        "student_id",
        "prediction_scope",
        "cutoff_timestamp",
        "data_origin",
    ],
}


def get_feature_compatibility_audit() -> Dict[str, Any]:
    """Return the formal feature compatibility audit report."""
    return {
        "subject_level": SUBJECT_LEVEL_AUDIT,
        "semester_level": SEMESTER_LEVEL_AUDIT,
        "summary": (
            "Models trained on the supported feature subset can be directly evaluated "
            "at inference using live outputs from mca_feature_extraction.py without "
            "missing-feature errors or invented synthetic defaults."
        ),
    }


# ===========================================================================
# Phase 2E Payload Adapters
# ===========================================================================

def adapt_phase2e_subject_payload(payload: Dict[str, Any]) -> pd.DataFrame:
    """
    Convert a Phase 2E subject-level feature extraction dictionary into a
    single-row DataFrame matching the model's supported feature columns.

    Args:
        payload: Return dictionary from extract_subject_academic_features().

    Returns:
        pd.DataFrame formatted for pipeline inference.
    """
    metadata = payload.get("metadata", {})
    features = payload.get("features", {})

    # Design score from Phase 2E is numeric 0-10; map to binary/numeric design_approved if > 0
    raw_design = features.get("design_score")
    design_val = 1.0 if (raw_design is not None and raw_design > 0) else (0.0 if raw_design is not None else None)

    # Synopsis approved to float
    raw_synopsis = features.get("synopsis_approved")
    synopsis_val = 1.0 if raw_synopsis is True else (0.0 if raw_synopsis is False else None)

    row = {
        "semester_number": metadata.get("target_semester", 1),
        "course_type": metadata.get("course_type", "theory"),
        "attendance_percentage": features.get("attendance_percentage"),
        "mst1_marks": features.get("mst1_marks"),
        "mst2_marks": features.get("mst2_marks"),
        "assignment_marks": features.get("assignment_score"),
        "prior_sgpa": features.get("latest_prior_sgpa"),
        "prior_cgpa": features.get("latest_declared_cgpa"),
        "viva_marks": features.get("viva_marks"),
        "lab_journal_marks": features.get("lab_record_score"),
        "synopsis_approved": synopsis_val,
        "design_approved": design_val,
        "implementation_percentage": features.get("implementation_pct"),
        "faculty_guide_interaction_score": features.get("supervisor_score"),
    }

    cols = SUBJECT_LEVEL_AUDIT["supported_features"]
    return pd.DataFrame([row])[cols]


def adapt_phase2e_semester_payload(payload: Dict[str, Any]) -> pd.DataFrame:
    """
    Convert a Phase 2E semester-level feature extraction dictionary into a
    single-row DataFrame matching the model's supported feature columns.

    Args:
        payload: Return dictionary from extract_semester_academic_features().

    Returns:
        pd.DataFrame formatted for pipeline inference.
    """
    metadata = payload.get("metadata", {})
    features = payload.get("features", {})

    row = {
        "semester_number": metadata.get("target_semester", 1),
        "courses_included": features.get("total_enrolled_courses", 0),
        "mean_attendance_percentage": features.get("average_attendance_percentage"),
        "mean_mst1_marks": features.get("average_mst1_marks"),
        "mean_mst2_marks": features.get("average_mst2_marks"),
        "mean_assignment_marks": features.get("average_assignment_score"),
        "mean_prior_sgpa": features.get("latest_prior_sgpa"),
        "mean_prior_cgpa": features.get("latest_declared_cgpa"),
    }

    cols = SEMESTER_LEVEL_AUDIT["supported_features"]
    return pd.DataFrame([row])[cols]
