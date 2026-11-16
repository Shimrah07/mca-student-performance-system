"""
backend/app/models/mca/__init__.py

Package export for all 13 MCA SQLAlchemy ORM models.
Adheres strictly to Phase 2B Final Implementation Contract.
"""

from app.models.mca.curriculum import (
    MCAProgram,
    MCACurriculumScheme,
    MCACourse,
    MCAAcademicSession,
    MCASessionCourse,
)
from app.models.mca.student import MCAStudent
from app.models.mca.registration import MCACourseRegistration
from app.models.mca.assessment import MCAAssessmentEvent
from app.models.mca.snapshot import (
    MCAAttendanceSnapshot,
    MCAFormativeSnapshot,
    MCAProjectMilestoneSnapshot,
)
from app.models.mca.history import MCASemesterResult
from app.models.mca.prediction import MCAPredictionRecord

__all__ = [
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
