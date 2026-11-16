"""
backend/app/seeders/__init__.py

Package initialization for canonical database seeders.
Seeders are never executed automatically; they require explicit invocation.
"""

from app.seeders.mca_curriculum_seeder import (
    seed_mca_curriculum,
    CurriculumSeederError,
    CurriculumSeedMismatchError,
    CANONICAL_PROGRAM,
    CANONICAL_SCHEMES,
    CANONICAL_COURSES,
)
from app.seeders.mca_demo_seeder import (
    seed_mca_demonstration_data,
    DemoSeederError,
    DemoSeederPrerequisiteError,
    DemoSeederMismatchError,
    DEMO_SESSION_SPEC,
    DEMO_STUDENTS_SPEC,
    DEMO_COURSE_CODES,
)

__all__ = [
    "seed_mca_curriculum",
    "CurriculumSeederError",
    "CurriculumSeedMismatchError",
    "CANONICAL_PROGRAM",
    "CANONICAL_SCHEMES",
    "CANONICAL_COURSES",
    "seed_mca_demonstration_data",
    "DemoSeederError",
    "DemoSeederPrerequisiteError",
    "DemoSeederMismatchError",
    "DEMO_SESSION_SPEC",
    "DEMO_STUDENTS_SPEC",
    "DEMO_COURSE_CODES",
]
