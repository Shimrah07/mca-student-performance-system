"""
backend/app/schemas/__init__.py

Exports all Pydantic request and response schemas.
"""

from app.schemas.prediction import (
    SubjectEnum,
    ScenarioEnum,
    StudentFeatures,
    PredictionRequest,
    PredictionResponse,
    PredictionHistoryItem,
    PredictionListResponse,
)
from app.schemas.mca import (
    McaSemester,
    McaCourseType,
    PredictionScope,
    McaScenario,
    VerificationStatus,
    PreviousDegree,
    McaCourseMetadata,
    McaSemesterMetadata,
    McaCurriculumResponse,
    TheoryAcademicFeatures,
    LabAcademicFeatures,
    ProjectAcademicFeatures,
    McaAcademicFeatures,
    McaSubjectPredictionRequest,
    McaCourseGradeInput,
    McaSemesterPredictionRequest,
    McaPredictionResponse,
)

__all__ = [
    "SubjectEnum",
    "ScenarioEnum",
    "StudentFeatures",
    "PredictionRequest",
    "PredictionResponse",
    "PredictionHistoryItem",
    "PredictionListResponse",
    "McaSemester",
    "McaCourseType",
    "PredictionScope",
    "McaScenario",
    "VerificationStatus",
    "PreviousDegree",
    "McaCourseMetadata",
    "McaSemesterMetadata",
    "McaCurriculumResponse",
    "TheoryAcademicFeatures",
    "LabAcademicFeatures",
    "ProjectAcademicFeatures",
    "McaAcademicFeatures",
    "McaSubjectPredictionRequest",
    "McaCourseGradeInput",
    "McaSemesterPredictionRequest",
    "McaPredictionResponse",
]

