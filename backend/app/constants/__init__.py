"""
backend/app/constants/__init__.py

Constants package for application-wide domain definitions.
"""

from app.constants.mca_curriculum import (
    MCA_PROGRAM_METADATA,
    MCA_SEMESTERS_DATA,
    get_mca_curriculum,
    get_all_mca_courses,
    get_mca_semester,
    get_mca_courses_by_semester,
    get_mca_course_by_id,
    get_mca_electives_by_semester,
)

__all__ = [
    "MCA_PROGRAM_METADATA",
    "MCA_SEMESTERS_DATA",
    "get_mca_curriculum",
    "get_all_mca_courses",
    "get_mca_semester",
    "get_mca_courses_by_semester",
    "get_mca_course_by_id",
    "get_mca_electives_by_semester",
]

