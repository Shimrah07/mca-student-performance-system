"""
ml/src/mca_dataset_loader.py

MCA Synthetic Dataset Loading and Validation Module.
Loads subject-level and semester-level synthetic datasets with schema enforcement,
label validation, null reporting, and strict isolation from production records.

Disclaimer:
This module operates exclusively on synthetic prototype datasets for model exploration.
It does not touch production student records or institutional databases.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd

# Standard allowed domains
VALID_PERFORMANCE_TIERS: Set[str] = {
    "Excellent",
    "Good",
    "Average",
    "Needs Improvement",
}

VALID_COURSE_TYPES: Set[str] = {
    "theory",
    "lab",
    "elective",
    "project",
}

# Required columns for each dataset scope
SUBJECT_LEVEL_REQUIRED_COLUMNS: List[str] = [
    "record_id",
    "student_id",
    "registration_id",
    "semester_number",
    "course_type",
    "prediction_scope",
    "cutoff_timestamp",
    "synthetic_final_score",
    "performance_tier",
]

SEMESTER_LEVEL_REQUIRED_COLUMNS: List[str] = [
    "record_id",
    "student_id",
    "semester_number",
    "prediction_scope",
    "cutoff_timestamp",
    "synthetic_semester_final_score",
    "performance_tier",
]

# Target outcome columns that must NEVER leak into model inputs
LEAKAGE_OUTCOME_COLUMNS: Set[str] = {
    "synthetic_final_score",
    "synthetic_semester_final_score",
}

IDENTIFIER_COLUMNS: Set[str] = {
    "record_id",
    "student_id",
    "registration_id",
    "data_origin",
}


# ===========================================================================
# Exceptions
# ===========================================================================

class DatasetLoaderError(Exception):
    """Base exception for dataset loading errors."""
    pass


class DatasetNotFoundError(DatasetLoaderError):
    """Raised when a required dataset CSV file cannot be located."""
    pass


class DatasetValidationError(DatasetLoaderError):
    """Raised when dataset rows fail schema, data type, or categorical domain validation."""
    pass


# ===========================================================================
# Path Resolution Helper
# ===========================================================================

def _resolve_dataset_path(filename: str, override_path: Optional[str] = None) -> Path:
    """
    Resolve dataset path, searching override path, ml/data/synthetic, and backend/data/synthetic.
    """
    if override_path:
        p = Path(override_path)
        if p.exists() and p.is_file():
            return p
        # If directory was passed
        if p.exists() and p.is_dir() and (p / filename).exists():
            return p / filename

    # Search candidates relative to current working directory or repository root
    candidates = [
        Path("ml/data/synthetic") / filename,
        Path("backend/data/synthetic") / filename,
        Path(__file__).resolve().parent.parent / "data" / "synthetic" / filename,
    ]

    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate

    raise DatasetNotFoundError(
        f"Synthetic dataset '{filename}' not found. "
        f"Searched paths: {[str(c) for c in candidates]}"
    )


# ===========================================================================
# Validation Utilities
# ===========================================================================

def validate_subject_level_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate subject-level dataset against schema, type, and domain rules.

    Returns:
        Structured validation report dictionary.

    Raises:
        DatasetValidationError: If validation fails.
    """
    if df.empty:
        raise DatasetValidationError("Subject-level dataset is empty.")

    # 1. Required columns
    missing_cols = [c for c in SUBJECT_LEVEL_REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        raise DatasetValidationError(f"Subject-level dataset missing required columns: {missing_cols}")

    # 2. Performance tier domain
    unique_tiers = set(df["performance_tier"].dropna().unique())
    invalid_tiers = unique_tiers - VALID_PERFORMANCE_TIERS
    if invalid_tiers:
        raise DatasetValidationError(
            f"Invalid performance_tier values found: {invalid_tiers}. "
            f"Allowed tiers: {sorted(VALID_PERFORMANCE_TIERS)}"
        )

    # 3. Missing target values
    null_targets = int(df["performance_tier"].isna().sum())
    if null_targets > 0:
        raise DatasetValidationError(f"Found {null_targets} rows with missing performance_tier.")

    # 4. Course type domain
    unique_types = set(df["course_type"].dropna().unique())
    invalid_types = unique_types - VALID_COURSE_TYPES
    if invalid_types:
        raise DatasetValidationError(
            f"Invalid course_type values found: {invalid_types}. "
            f"Allowed types: {sorted(VALID_COURSE_TYPES)}"
        )

    # 5. Prediction scope validation
    unique_scopes = set(df["prediction_scope"].dropna().unique())
    if unique_scopes != {"subject"}:
        raise DatasetValidationError(
            f"Subject-level dataset contains unexpected prediction_scope values: {unique_scopes}"
        )

    # 6. Semester number range
    invalid_sems = df[~df["semester_number"].isin([1, 2, 3, 4])]
    if not invalid_sems.empty:
        raise DatasetValidationError(
            f"Found {len(invalid_sems)} rows with invalid semester_number (must be 1-4)."
        )

    # 7. Generate report
    null_counts = df.isna().sum().to_dict()
    null_dict = {k: int(v) for k, v in null_counts.items() if v > 0}
    total_nulls = sum(null_dict.values())
    tier_dist = df["performance_tier"].value_counts().to_dict()
    course_type_dist = df["course_type"].value_counts().to_dict()

    return {
        "scope": "subject",
        "row_count": len(df),
        "total_rows": len(df),
        "column_count": len(df.columns),
        "total_columns": len(df.columns),
        "unique_students": int(df["student_id"].nunique()),
        "unique_registrations": int(df["registration_id"].nunique()),
        "performance_tier_distribution": tier_dist,
        "course_type_distribution": course_type_dist,
        "null_counts": null_dict,
        "null_count": total_nulls,
    }


def validate_semester_level_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate semester-level dataset against schema, type, and domain rules.

    Returns:
        Structured validation report dictionary.

    Raises:
        DatasetValidationError: If validation fails.
    """
    if df.empty:
        raise DatasetValidationError("Semester-level dataset is empty.")

    # 1. Required columns
    missing_cols = [c for c in SEMESTER_LEVEL_REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        raise DatasetValidationError(f"Semester-level dataset missing required columns: {missing_cols}")

    # 2. Performance tier domain
    unique_tiers = set(df["performance_tier"].dropna().unique())
    invalid_tiers = unique_tiers - VALID_PERFORMANCE_TIERS
    if invalid_tiers:
        raise DatasetValidationError(
            f"Invalid performance_tier values found: {invalid_tiers}. "
            f"Allowed tiers: {sorted(VALID_PERFORMANCE_TIERS)}"
        )

    # 3. Missing target values
    null_targets = int(df["performance_tier"].isna().sum())
    if null_targets > 0:
        raise DatasetValidationError(f"Found {null_targets} rows with missing performance_tier.")

    # 4. Prediction scope validation
    unique_scopes = set(df["prediction_scope"].dropna().unique())
    if unique_scopes != {"semester"}:
        raise DatasetValidationError(
            f"Semester-level dataset contains unexpected prediction_scope values: {unique_scopes}"
        )

    # 5. Semester number range
    invalid_sems = df[~df["semester_number"].isin([1, 2, 3, 4])]
    if not invalid_sems.empty:
        raise DatasetValidationError(
            f"Found {len(invalid_sems)} rows with invalid semester_number (must be 1-4)."
        )

    # 6. Generate report
    null_counts = df.isna().sum().to_dict()
    null_dict = {k: int(v) for k, v in null_counts.items() if v > 0}
    total_nulls = sum(null_dict.values())
    tier_dist = df["performance_tier"].value_counts().to_dict()

    return {
        "scope": "semester",
        "row_count": len(df),
        "total_rows": len(df),
        "column_count": len(df.columns),
        "total_columns": len(df.columns),
        "unique_students": int(df["student_id"].nunique()),
        "performance_tier_distribution": tier_dist,
        "null_counts": null_dict,
        "null_count": total_nulls,
    }


def validate_dataset_schema(df: pd.DataFrame, scope: str = "subject") -> Dict[str, Any]:
    """
    Unified validation dispatcher for subject-level or semester-level datasets.
    """
    if scope == "subject":
        return validate_subject_level_dataframe(df)
    elif scope == "semester":
        return validate_semester_level_dataframe(df)
    else:
        raise ValueError(f"Unknown scope: {scope}. Must be 'subject' or 'semester'.")


# ===========================================================================
# Dataset Loaders
# ===========================================================================

def load_subject_level_dataset(
    csv_path: Optional[str] = None,
    validate: bool = True,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Load and optionally validate the subject-level synthetic MCA dataset.

    Args:
        csv_path: Optional explicit file path. If None, resolves default path.
        validate: If True, performs rigorous schema and domain validation.

    Returns:
        (DataFrame, validation_report_dict)
    """
    resolved_path = _resolve_dataset_path("mca_synthetic_subject_level.csv", csv_path)
    df = pd.read_csv(resolved_path)

    report = {}
    if validate:
        report = validate_subject_level_dataframe(df)

    return df, report


def load_semester_level_dataset(
    csv_path: Optional[str] = None,
    validate: bool = True,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Load and optionally validate the semester-level synthetic MCA dataset.

    Args:
        csv_path: Optional explicit file path. If None, resolves default path.
        validate: If True, performs rigorous schema and domain validation.

    Returns:
        (DataFrame, validation_report_dict)
    """
    resolved_path = _resolve_dataset_path("mca_synthetic_semester_level.csv", csv_path)
    df = pd.read_csv(resolved_path)

    report = {}
    if validate:
        report = validate_semester_level_dataframe(df)

    return df, report
