"""
backend/app/schemas/prediction.py

Pydantic schemas for student performance prediction requests and responses.

Validation Safeguards:
- Strict leakage prevention: rejects target-leaking fields G2 and G3.
- Scenario A (Early-Warning) excludes G1 from input features.
- Scenario B (Mid-Term) requires G1 (0-20 scale).
- Full feature validation matching the UCI Student Performance dataset schema.
- Explicit labelling of probabilities as indicative, uncalibrated model estimates.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, model_validator


class SubjectEnum(str, Enum):
    MATHEMATICS = "Mathematics"
    PORTUGUESE = "Portuguese"


class ScenarioEnum(str, Enum):
    SCENARIO_A = "Scenario A"
    SCENARIO_B = "Scenario B"


class StudentFeatures(BaseModel):
    """
    Input feature attributes for a student based on the UCI dataset.
    """
    # 13 binary attributes
    school: Literal["GP", "MS"] = Field(..., description="Student school ('GP' - Gabriel Pereira or 'MS' - Mousinho da Silveira)")
    sex: Literal["F", "M"] = Field(..., description="Student gender ('F' - female or 'M' - male)")
    address: Literal["U", "R"] = Field(..., description="Home address type ('U' - urban or 'R' - rural)")
    famsize: Literal["LE3", "GT3"] = Field(..., description="Family size ('LE3' - <= 3 or 'GT3' - > 3)")
    Pstatus: Literal["T", "A"] = Field(..., description="Parent cohabitation status ('T' - together or 'A' - apart)")
    schoolsup: Literal["yes", "no"] = Field(..., description="Extra educational support ('yes' or 'no')")
    famsup: Literal["yes", "no"] = Field(..., description="Family educational support ('yes' or 'no')")
    paid: Literal["yes", "no"] = Field(..., description="Extra paid classes ('yes' or 'no')")
    activities: Literal["yes", "no"] = Field(..., description="Extra-curricular activities ('yes' or 'no')")
    nursery: Literal["yes", "no"] = Field(..., description="Attended nursery school ('yes' or 'no')")
    higher: Literal["yes", "no"] = Field(..., description="Wants to take higher education ('yes' or 'no')")
    internet: Literal["yes", "no"] = Field(..., description="Internet access at home ('yes' or 'no')")
    romantic: Literal["yes", "no"] = Field(..., description="In a romantic relationship ('yes' or 'no')")

    # 4 nominal multi-category attributes
    Mjob: Literal["teacher", "health", "services", "at_home", "other"] = Field(..., description="Mother's job")
    Fjob: Literal["teacher", "health", "services", "at_home", "other"] = Field(..., description="Father's job")
    reason: Literal["home", "reputation", "course", "other"] = Field(..., description="Reason to choose this school")
    guardian: Literal["mother", "father", "other"] = Field(..., description="Student's guardian")

    # 11 ordinal survey attributes
    Medu: int = Field(..., ge=0, le=4, description="Mother's education (0=none, 1=primary 4th grade, 2=5th-9th, 3=secondary, 4=higher)")
    Fedu: int = Field(..., ge=0, le=4, description="Father's education (0=none, 1=primary 4th grade, 2=5th-9th, 3=secondary, 4=higher)")
    traveltime: int = Field(..., ge=1, le=4, description="Home to school travel time (1=<15 min, 2=15-30 min, 3=30-60 min, 4=>60 min)")
    studytime: int = Field(..., ge=1, le=4, description="Weekly study time (1=<2 hours, 2=2-5 hours, 3=5-10 hours, 4=>10 hours)")
    failures: int = Field(..., ge=0, le=4, description="Number of past class failures (0 to 4)")
    famrel: int = Field(..., ge=1, le=5, description="Quality of family relationships (1=very bad to 5=excellent)")
    freetime: int = Field(..., ge=1, le=5, description="Free time after school (1=very low to 5=very high)")
    goout: int = Field(..., ge=1, le=5, description="Going out with friends (1=very low to 5=very high)")
    Dalc: int = Field(..., ge=1, le=5, description="Workday alcohol consumption (1=very low to 5=very high)")
    Walc: int = Field(..., ge=1, le=5, description="Weekend alcohol consumption (1=very low to 5=very high)")
    health: int = Field(..., ge=1, le=5, description="Current health status (1=very bad to 5=very good)")

    # 2 continuous/count attributes
    age: int = Field(..., ge=15, le=22, description="Student's age (15 to 22)")
    absences: int = Field(..., ge=0, le=93, description="Number of school absences (0 to 93)")

    # Optional First Period Grade (G1) — required only in Scenario B
    G1: Optional[float] = Field(None, ge=0, le=20, description="Period 1 exam grade (0-20 scale); required for Scenario B")

    # Disallowed fields will be caught by model_validator
    model_config = {
        "extra": "allow",  # Allow extra to explicitly detect and reject G2 and G3
    }

    @model_validator(mode="before")
    @classmethod
    def check_for_leaking_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for field in ("G2", "G3", "g2", "g3"):
                if field in data:
                    raise ValueError(
                        f"Data leakage detected: '{field}' is strictly disallowed as a model input."
                    )
        return data


class PredictionRequest(BaseModel):
    """
    Request payload for student performance prediction.
    """
    subject: SubjectEnum = Field(..., description="Subject ('Mathematics' or 'Portuguese')")
    scenario: ScenarioEnum = Field(..., description="Scenario ('Scenario A' or 'Scenario B')")
    features: StudentFeatures = Field(..., description="Student demographic, academic, and behavioral features")
    student_code: Optional[str] = Field(
        None,
        description="Optional anonymized student identifier (e.g. 'STU-001') to link prediction history",
    )

    @model_validator(mode="after")
    def validate_scenario_requirements(self) -> "PredictionRequest":
        """
        Ensure Scenario A does not require G1, and Scenario B strictly requires G1.
        """
        if self.scenario == ScenarioEnum.SCENARIO_B:
            if self.features.G1 is None:
                raise ValueError("Scenario B (Mid-Term) requires 'G1' (first-period grade between 0 and 20).")
        return self


class PredictionResponse(BaseModel):
    """
    Complete response containing predicted category, uncalibrated probabilities,
    structured rule-based recommendations, and persistence metadata.
    """
    predicted_category: str = Field(..., description="Predicted performance category ('Excellent', 'Good', 'Average', 'Needs Improvement')")
    subject: str = Field(..., description="Evaluated subject ('Mathematics' or 'Portuguese')")
    scenario: str = Field(..., description="Evaluated scenario ('Scenario A' or 'Scenario B')")
    model_name: str = Field(..., description="Name of candidate classifier used")
    model_version: str = Field(..., description="Version of model artifact")
    prediction_probabilities: Optional[Dict[str, float]] = Field(
        None,
        description="Indicative class probability estimates (uncalibrated)",
    )
    probabilities_note: str = Field(
        "Indicative model estimates only. Probabilities are uncalibrated and do not represent guaranteed real-world risk.",
        description="Pedagogical disclaimer regarding probabilistic outputs",
    )
    summary: str = Field(..., description="Category-level strategic advice summary")
    actionable_recommendations: List[str] = Field(..., description="Actionable recommendations tailored to student indicators")
    strengths_identified: List[str] = Field(..., description="Recognized academic and behavioral strengths")
    evaluated_factors: Dict[str, Any] = Field(..., description="Input factors that triggered specific recommendations")
    disclaimer: str = Field(..., description="Safety and pedagogical disclaimer")
    prediction_id: Optional[int] = Field(None, description="Database record ID if successfully persisted")
    persisted: bool = Field(False, description="True if the prediction was saved to the database")
    created_at: Optional[datetime] = Field(None, description="Timestamp of prediction event")


class PredictionHistoryItem(BaseModel):
    """
    Schema for viewing a previously persisted prediction record.
    """
    id: int
    student_id: Optional[int] = None
    subject: str
    scenario: str
    model_name: str
    model_version: str
    predicted_category: str
    prediction_probabilities: Optional[Dict[str, float]] = None
    input_features: Dict[str, Any]
    weak_areas: Optional[List[str]] = None
    recommendations: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None


class PredictionListResponse(BaseModel):
    """
    Paginated list of prediction history records.
    """
    total: int
    items: List[PredictionHistoryItem]
