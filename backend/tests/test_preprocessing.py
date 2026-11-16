"""
backend/tests/test_preprocessing.py

Automated test suite verifying the Stage 2 data preprocessing pipeline:
- Correct target mapping and boundary score checks (0, 9, 10, 13, 14, 15, 16, 20)
- Out-of-bounds score error handling
- Feature taxonomy validation against both raw datasets (33 columns accounted for)
- Strict leakage prevention: G3, G2, and G1 exclusion in Scenario A; G3 and G2 exclusion in Scenario B
- Stratified 80/20 train/test splitting with representation of all 4 classes
- Successful fit on training data and transform on test data without NaN values
- Robust handling of unseen categorical values during inference
- Verification that raw CSV files remain pristine and unmodified
"""

import sys
from pathlib import Path

# Ensure project root is first in sys.path so ml package is always discoverable
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
import pandas as pd
import numpy as np

from ml.src.preprocessing import (
    CATEGORICAL_FEATURES,
    NUMERICAL_FEATURES_SCENARIO_A,
    NUMERICAL_FEATURES_SCENARIO_B,
    ALL_DATASET_COLUMNS,
    PERFORMANCE_CATEGORIES,
    map_grade_to_category,
    load_raw_dataset,
    prepare_features_and_target,
    build_preprocessor,
    build_preprocessing_pipeline,
    split_data,
)

# Resolve dataset paths relative to project root
MATH_CSV = PROJECT_ROOT / "ml" / "data" / "student-mat.csv"
POR_CSV = PROJECT_ROOT / "ml" / "data" / "student-por.csv"


# ---------------------------------------------------------------------------
# 1. Target mapping & boundary tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "grade, expected_category",
    [
        # Boundary test cases required by project specification
        (0, "Needs Improvement"),
        (9, "Needs Improvement"),
        (10, "Average"),
        (13, "Average"),
        (14, "Good"),
        (15, "Good"),
        (16, "Excellent"),
        (20, "Excellent"),
        # Intermediate test cases
        (5, "Needs Improvement"),
        (11, "Average"),
        (12, "Average"),
        (14.5, "Good"),
        (17, "Excellent"),
        (19.5, "Excellent"),
    ],
)
def test_map_grade_to_category_boundaries(grade, expected_category):
    """Verify exact boundary mapping from 0-20 numeric grades to 4 categories."""
    assert map_grade_to_category(grade) == expected_category


@pytest.mark.parametrize("invalid_grade", [-1, -0.1, 20.1, 25, 100, float("nan")])
def test_map_grade_to_category_invalid_raises_error(invalid_grade):
    """Verify that grades outside [0, 20] or NaN raise ValueError."""
    with pytest.raises(ValueError):
        map_grade_to_category(invalid_grade)


# ---------------------------------------------------------------------------
# 2. Dataset loading and column taxonomy tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("csv_path, expected_rows", [(MATH_CSV, 395), (POR_CSV, 649)])
def test_load_raw_dataset_and_column_integrity(csv_path, expected_rows):
    """Verify that raw CSV files load with exactly 33 columns and expected row count."""
    df = load_raw_dataset(csv_path)
    assert len(df) == expected_rows
    assert df.shape[1] == 33

    # Check that our taxonomy covers 100% of the columns in the CSV
    assert set(df.columns) == set(ALL_DATASET_COLUMNS)

    # Check categorical column types (all should be string or object dtype)
    for col in CATEGORICAL_FEATURES:
        assert pd.api.types.is_string_dtype(df[col]), f"Column {col} expected string/object dtype"

    # Check numerical column types (all should be integer/numeric)
    for col in NUMERICAL_FEATURES_SCENARIO_A:
        assert np.issubdtype(df[col].dtype, np.number), f"Column {col} expected numeric dtype"


# ---------------------------------------------------------------------------
# 3. Leakage safety & scenario separation tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("csv_path", [MATH_CSV, POR_CSV])
def test_scenario_a_feature_exclusion_safety(csv_path):
    """
    Scenario A (Early-Warning):
    Must exclude G1, G2, and G3 from feature matrix X.
    Must have exactly 30 features (17 categorical + 13 numerical).
    """
    df = load_raw_dataset(csv_path)
    X, y = prepare_features_and_target(df, scenario="A")

    # Strict leakage assertions
    assert "G3" not in X.columns, "Data Leakage: G3 found in Scenario A features!"
    assert "G2" not in X.columns, "Data Leakage: G2 found in Scenario A features!"
    assert "G1" not in X.columns, "Data Leakage: G1 found in Scenario A features!"

    assert X.shape[1] == 30
    assert len(X) == len(df)
    assert len(y) == len(df)
    assert set(y.unique()).issubset(set(PERFORMANCE_CATEGORIES))


@pytest.mark.parametrize("csv_path", [MATH_CSV, POR_CSV])
def test_scenario_b_feature_inclusion_and_safety(csv_path):
    """
    Scenario B (Mid-Term Diagnostic):
    Must exclude G2 and G3 from feature matrix X.
    Must include G1 as an early diagnostic feature.
    Must have exactly 31 features (17 categorical + 14 numerical).
    """
    df = load_raw_dataset(csv_path)
    X, y = prepare_features_and_target(df, scenario="B")

    # Strict leakage assertions
    assert "G3" not in X.columns, "Data Leakage: G3 found in Scenario B features!"
    assert "G2" not in X.columns, "Data Leakage: G2 found in Scenario B features!"
    assert "G1" in X.columns, "Scenario B must include G1 as an early diagnostic feature!"

    assert X.shape[1] == 31
    assert len(X) == len(df)
    assert len(y) == len(df)
    assert set(y.unique()).issubset(set(PERFORMANCE_CATEGORIES))


def test_invalid_scenario_raises_error():
    """Verify that unsupported scenario string raises ValueError."""
    df = load_raw_dataset(MATH_CSV)
    with pytest.raises(ValueError):
        prepare_features_and_target(df, scenario="C")


# ---------------------------------------------------------------------------
# 4. Stratified train/test split tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("csv_path, expected_train, expected_test", [
    (MATH_CSV, 316, 79),
    (POR_CSV, 519, 130),
])
@pytest.mark.parametrize("scenario", ["A", "B"])
def test_stratified_split_preserves_classes(csv_path, expected_train, expected_test, scenario):
    """
    Verify 80/20 train/test split sizes and confirm that all 4 classes
    are present in both the training set and the test set.
    """
    df = load_raw_dataset(csv_path)
    X, y = prepare_features_and_target(df, scenario=scenario)

    X_train, X_test, y_train, y_test = split_data(X, y, test_size=0.20, random_state=42)

    assert len(X_train) == expected_train
    assert len(X_test) == expected_test
    assert len(y_train) == expected_train
    assert len(y_test) == expected_test

    # Verify that all 4 categories are represented in both train and test partitions
    train_classes = set(y_train.unique())
    test_classes = set(y_test.unique())

    assert train_classes == set(PERFORMANCE_CATEGORIES)
    assert test_classes == set(PERFORMANCE_CATEGORIES)


# ---------------------------------------------------------------------------
# 5. Preprocessor fit/transform tests & unseen category handling
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("scenario, expected_num_features", [("A", 13), ("B", 14)])
def test_preprocessor_fit_transform_on_splits(scenario, expected_num_features):
    """
    Verify that the ColumnTransformer fits on training data and transforms
    both train and test splits without producing NaN values.
    """
    df = load_raw_dataset(MATH_CSV)
    X, y = prepare_features_and_target(df, scenario=scenario)
    X_train, X_test, _, _ = split_data(X, y, test_size=0.20, random_state=42)

    preprocessor = build_preprocessor(scenario=scenario)

    # Fit ONLY on training data
    preprocessor.fit(X_train)

    X_train_trans = preprocessor.transform(X_train)
    X_test_trans = preprocessor.transform(X_test)

    # Ensure output is a 2D numpy array with no NaNs
    assert isinstance(X_train_trans, np.ndarray)
    assert isinstance(X_test_trans, np.ndarray)
    assert not np.isnan(X_train_trans).any(), "NaN values found in transformed X_train!"
    assert not np.isnan(X_test_trans).any(), "NaN values found in transformed X_test!"

    # Transformed columns must be identical between train and test
    assert X_train_trans.shape[1] == X_test_trans.shape[1]
    assert X_train_trans.shape[0] == len(X_train)
    assert X_test_trans.shape[0] == len(X_test)


def test_preprocessor_handles_unseen_categories():
    """
    Verify that OneHotEncoder with handle_unknown='ignore' gracefully handles
    unseen categories in test data by encoding them as all-zeros without throwing errors.
    """
    df = load_raw_dataset(MATH_CSV)
    X, y = prepare_features_and_target(df, scenario="A")
    X_train, X_test, _, _ = split_data(X, y, test_size=0.20, random_state=42)

    preprocessor = build_preprocessor(scenario="A")
    preprocessor.fit(X_train)

    # Create a synthetic sample with completely unseen nominal categories
    unseen_sample = X_test.iloc[[0]].copy()
    unseen_sample["school"] = "UNKNOWN_SCHOOL"
    unseen_sample["Mjob"] = "astronaut"
    unseen_sample["reason"] = "teleportation"
    unseen_sample["guardian"] = "alien"

    # Should transform cleanly without error
    transformed = preprocessor.transform(unseen_sample)
    assert isinstance(transformed, np.ndarray)
    assert not np.isnan(transformed).any()
    assert transformed.shape[1] == preprocessor.transform(X_train).shape[1]


def test_build_preprocessing_pipeline():
    """Verify that build_preprocessing_pipeline wraps the transformer in a valid Pipeline."""
    pipeline = build_preprocessing_pipeline(scenario="A")
    df = load_raw_dataset(MATH_CSV)
    X, y = prepare_features_and_target(df, scenario="A")
    X_train, X_test, _, _ = split_data(X, y, test_size=0.20, random_state=42)

    pipeline.fit(X_train)
    out = pipeline.transform(X_test)
    assert isinstance(out, np.ndarray)
    assert out.shape[0] == len(X_test)


# ---------------------------------------------------------------------------
# 6. Verification that raw CSV files were not modified
# ---------------------------------------------------------------------------

def test_raw_csv_files_unmodified():
    """Confirm line count and integrity of source CSV files in ml/data/."""
    with open(MATH_CSV, "r", encoding="utf-8") as f:
        mat_lines = len(f.readlines())
    with open(POR_CSV, "r", encoding="utf-8") as f:
        por_lines = len(f.readlines())

    assert mat_lines == 396, f"Expected 396 lines (header + 395 rows) in Math CSV. Found: {mat_lines}"
    assert por_lines == 650, f"Expected 650 lines (header + 649 rows) in Por CSV. Found: {por_lines}"
