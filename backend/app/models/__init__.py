"""
backend/app/models/__init__.py

Exports all SQLAlchemy ORM models and declarative Base.
Includes Phase 1 UCI benchmark models and Phase 2B MCA curriculum models.
"""

from app.database import Base
from app.models.student import Student
from app.models.prediction import PredictionRecord

# Phase 2B MCA Models
from app.models.mca import (
    MCAProgram,
    MCACurriculumScheme,
    MCACourse,
    MCAAcademicSession,
    MCASessionCourse,
    MCAStudent,
    MCACourseRegistration,
    MCAAssessmentEvent,
    MCAAttendanceSnapshot,
    MCAFormativeSnapshot,
    MCAProjectMilestoneSnapshot,
    MCASemesterResult,
    MCAPredictionRecord,
)

__all__ = [
    # Declarative Base
    "Base",
    # Phase 1 UCI Models
    "Student",
    "PredictionRecord",
    # Phase 2B MCA Models
    "MCAProgram",
    "MCACurriculumScheme",
    "MCACourse",
    "MCAAcademicSession",
    "MCASessionCourse",
    "MCAStudent",
    "MCACourseRegistration",
    "MCAAssessmentEvent",
    "MCAAttendanceSnapshot",
    "MCAFormativeSnapshot",
    "MCAProjectMilestoneSnapshot",
    "MCASemesterResult",
    "MCAPredictionRecord",
]
