"""
ml/src/preprocessing.py

Data loading, target categorization, train/test splitting, and feature
preprocessing pipelines for the AI-Based Student Performance Prediction System.

This module enforces strict data leakage prevention:
- Target is computed from G3 using the approved 4 categories.
- G3 is NEVER included in feature matrix X.
- G2 is NEVER included in feature matrix X.
- G1 is excluded in Scenario A (Early-Warning) and included in Scenario B (Mid-Term).
- Preprocessors are fitted ONLY on training data.
"""

from pathlib import Path
from typing import Literal, Tuple
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# ---------------------------------------------------------------------------
# Approved feature taxonomy (30 non-grade attributes in UCI dataset)
# ---------------------------------------------------------------------------

CATEGORICAL_FEATURES = [
    # 13 binary features
    "school",
    "sex",
    "address",
    "famsize",
    "Pstatus",
    "schoolsup",
    "famsup",
    "paid",
    "activities",
    "nursery",
    "higher",
    "internet",
    "romantic",
    # 4 nominal multi-category features
    "Mjob",
    "Fjob",
    "reason",
    "guardian",
]

NUMERICAL_FEATURES_SCENARIO_A = [
    # 11 ordinal survey features
    "Medu",
    "Fedu",
    "traveltime",
    "studytime",
    "failures",
    "famrel",
    "freetime",
    "goout",
    "Dalc",
    "Walc",
    "health",
    # 2 continuous / count features
    "age",
    "absences",
]

# Scenario B incorporates Period 1 exam (G1) as an early diagnostic indicator
NUMERICAL_FEATURES_SCENARIO_B = NUMERICAL_FEATURES_SCENARIO_A + ["G1"]

# All 33 columns expected in raw CSV files
ALL_DATASET_COLUMNS = (
    CATEGORICAL_FEATURES
    + NUMERICAL_FEATURES_SCENARIO_A
    + ["G1", "G2", "G3"]
)

# Approved target categories (ordered from lowest to highest achievement)
PERFORMANCE_CATEGORIES = [
    "Needs Improvement",
    "Average",
    "Good",
    "Excellent",
]


# ---------------------------------------------------------------------------
# Target mapping function
# ---------------------------------------------------------------------------

def map_grade_to_category(grade: int | float) -> str:
    """
    Map an integer or float grade on a 0-20 scale to one of four
    performance categories:
      - 16 to 20: Excellent
      - 14 to 15: Good
      - 10 to 13: Average
      -  0 to  9: Needs Improvement

    Raises ValueError if grade is outside [0, 20].
    """
    if pd.isna(grade):
        raise ValueError("Grade cannot be NaN.")
    if grade < 0 or grade > 20:
        raise ValueError(f"Grade must be between 0 and 20. Received: {grade}")

    if grade >= 16:
        return "Excellent"
    elif grade >= 14:
        return "Good"
    elif grade >= 10:
        return "Average"
    else:
        return "Needs Improvement"


# ---------------------------------------------------------------------------
# Dataset loading and scenario feature extraction
# ---------------------------------------------------------------------------

def load_raw_dataset(filepath: str | Path) -> pd.DataFrame:
    """
    Read raw student dataset from CSV using semicolon delimiter.
    Verifies that all 33 expected columns exist and data is not empty.
    """
    path = Path(filepath)
    if not path.is_file():
        raise FileNotFoundError(f"Dataset file not found at: {path.resolve()}")

    df = pd.read_csv(path, sep=";")

    # Verify column completeness
    missing_cols = set(ALL_DATASET_COLUMNS) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Dataset is missing required columns: {missing_cols}")

    return df


def prepare_features_and_target(
    df: pd.DataFrame, scenario: Literal["A", "B"] = "A"
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Prepare feature matrix X and target series y for a given prediction scenario.

    Parameters:
      df: Raw dataframe containing all 33 columns.
      scenario:
        - 'A' (Early-Warning): Excludes G1, G2, G3. 30 features.
        - 'B' (Mid-Term): Excludes G2, G3. Includes G1. 31 features.

    Returns:
      (X, y):
        X is a DataFrame with clean feature columns.
        y is a Series of strings representing the 4 performance categories.
    """
    scenario_clean = scenario.upper().strip()
    if scenario_clean not in ("A", "B"):
        raise ValueError(
            f"Invalid scenario '{scenario}'. Must be 'A' (Early-Warning) or 'B' (Mid-Term)."
        )

    # 1. Derive target from G3
    y = df["G3"].apply(map_grade_to_category)
    y.name = "performance_category"

    # 2. Extract feature columns strictly based on scenario
    if scenario_clean == "A":
        feature_cols = CATEGORICAL_FEATURES + NUMERICAL_FEATURES_SCENARIO_A
    else:
        feature_cols = CATEGORICAL_FEATURES + NUMERICAL_FEATURES_SCENARIO_B

    X = df[feature_cols].copy()

    # 3. Explicit leakage assertions
    assert "G3" not in X.columns, "Fatal error: G3 leaked into feature matrix X!"
    assert "G2" not in X.columns, "Fatal error: G2 leaked into feature matrix X!"
    if scenario_clean == "A":
        assert "G1" not in X.columns, "Fatal error: G1 leaked into Scenario A feature matrix X!"
    else:
        assert "G1" in X.columns, "Scenario B must include G1 as an early diagnostic feature."

    return X, y


# ---------------------------------------------------------------------------
# Preprocessor construction
# ---------------------------------------------------------------------------

def build_preprocessor(scenario: Literal["A", "B"] = "A") -> ColumnTransformer:
    """
    Build a scikit-learn ColumnTransformer for the specified scenario:
      - Categorical features -> OneHotEncoder(handle_unknown='ignore', sparse_output=False)
      - Numerical/Ordinal features -> StandardScaler()

    The preprocessor is returned unfitted. It must be fitted ONLY on training data.
    """
    scenario_clean = scenario.upper().strip()
    if scenario_clean not in ("A", "B"):
        raise ValueError(f"Invalid scenario '{scenario}'. Must be 'A' or 'B'.")

    categorical_cols = CATEGORICAL_FEATURES
    if scenario_clean == "A":
        numerical_cols = NUMERICAL_FEATURES_SCENARIO_A
    else:
        numerical_cols = NUMERICAL_FEATURES_SCENARIO_B

    categorical_transformer = OneHotEncoder(
        handle_unknown="ignore",
        sparse_output=False,
    )
    numerical_transformer = StandardScaler()

    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", categorical_transformer, categorical_cols),
            ("num", numerical_transformer, numerical_cols),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )

    return preprocessor


def build_preprocessing_pipeline(
    scenario: Literal["A", "B"] = "A",
) -> Pipeline:
    """
    Wrap the ColumnTransformer in a scikit-learn Pipeline so it can be fitted,
    serialized, and easily chained with classifiers in Stage 2/3.
    """
    preprocessor = build_preprocessor(scenario=scenario)
    return Pipeline(steps=[("preprocessor", preprocessor)])


# ---------------------------------------------------------------------------
# Stratified train/test splitting
# ---------------------------------------------------------------------------

def split_data(
    X: pd.DataFrame,
    y: pd.Series,
    test_size: float = 0.20,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Perform a stratified train/test split.

    Stratification ensures that all 4 categories (especially the minority
    'Excellent' class) are represented proportionally in both sets.
    """
    return train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y,
    )
