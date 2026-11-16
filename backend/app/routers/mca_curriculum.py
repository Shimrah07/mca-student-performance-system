"""
backend/app/routers/mca_curriculum.py

Read-only API router for the Master of Computer Applications (MCA) curriculum
at University Institute of Technology — RGPV (Autonomous), Bhopal.

Endpoints:
- GET /api/mca/curriculum : Complete 4-semester curriculum (26 confirmed courses).
- GET /api/mca/semesters/{semester_number} : Specific semester course roster.

Design Principles:
- Read-only additive router.
- Reuses canonical backend curriculum constants and Pydantic schemas (no data duplication).
- Preserves nullable course codes and credits where unverified.
- Preserves confirmed elective groups and course archetypes.
"""

from fastapi import APIRouter, HTTPException, Path, status

from app.constants.mca_curriculum import (
    get_mca_curriculum,
    get_mca_semester,
)
from app.schemas.mca import (
    McaCurriculumResponse,
    McaSemesterMetadata,
)

router = APIRouter(tags=["MCA Curriculum"])


@router.get(
    "/curriculum",
    response_model=McaCurriculumResponse,
    summary="Get complete MCA curriculum",
    response_description="Complete 4-semester MCA curriculum including all 26 courses.",
    responses={
        status.HTTP_200_OK: {
            "description": "Curriculum successfully retrieved.",
        },
    },
)
def get_curriculum() -> McaCurriculumResponse:
    """
    Retrieve the formal MCA curriculum across all four semesters.

    Returns institutional metadata, all 4 semesters, and all 26 confirmed courses
    with course types, elective group associations, and verification audit notes.
    """
    return get_mca_curriculum()


@router.get(
    "/semesters/{semester_number}",
    response_model=McaSemesterMetadata,
    summary="Get specific MCA semester curriculum",
    response_description="Curriculum metadata and enrolled course roster for the requested semester.",
    responses={
        status.HTTP_200_OK: {
            "description": "Semester curriculum successfully retrieved.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Semester not found (valid semesters are 1 through 4).",
        },
    },
)
def get_semester(
    semester_number: int = Path(
        ...,
        description="MCA Semester number (1 to 4)",
        examples=[1, 2, 3, 4],
    ),
) -> McaSemesterMetadata:
    """
    Retrieve curriculum metadata and subjects for a specific MCA semester.

    Validation rules:
    - Accepts semester numbers 1 through 4 only.
    - Returns HTTP 404 if the semester number is outside 1 to 4.
    """
    if semester_number < 1 or semester_number > 4:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Semester {semester_number} not found. Valid MCA semesters are 1 through 4.",
        )

    semester = get_mca_semester(semester_number)
    if not semester:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Semester {semester_number} not found. Valid MCA semesters are 1 through 4.",
        )

    return semester
