"""
backend/app/seeders/mca_curriculum_seeder.py

Idempotent, non-destructive canonical MCA curriculum seeder for University
Institute of Technology — RGPV (Autonomous), Bhopal.

Authoritative Architecture:
- Phase2B_Final_Implementation_Contract.md
- backend/app/constants/mca_curriculum.py

Seeder Scope:
- Populates one canonical MCA program (MCA).
- Populates the two officially verified curriculum schemes:
    * MCA-AUTONOMOUS-2025 (Official scheme effective July 2025, governing Semester 1)
    * MCA-AUTONOMOUS-2024 (Official scheme effective July 2024, governing Semester 3)
- Populates all 26 canonical courses across 4 semesters (7 / 7 / 7 / 5):
    * Semester 1 (7 courses): verified codes, verified credits, mapped to MCA-AUTONOMOUS-2025.
    * Semester 2 (7 courses): provisional (code=NULL, credits=NULL, scheme_id=NULL).
    * Semester 3 (7 courses): verified codes, verified credits, mapped to MCA-AUTONOMOUS-2024.
    * Semester 4 (5 courses): provisional (code=NULL, credits=NULL, scheme_id=NULL).

Non-Destructive & Idempotent Rules:
1. If a canonical record does not exist, insert it.
2. If it exists and matches approved canonical data, leave it unchanged.
3. If it exists but differs from canonical data, raise CurriculumSeedMismatchError
   and abort the transaction with a full rollback.
4. Never silently overwrite existing records.
5. Never delete existing records.
6. Never modify historical records.
7. Never create duplicate records.
8. No academic sessions, session courses, students, registrations, or predictions created.

Execution:
- Explicit execution only. Never run automatically during application startup or import.
"""

import argparse
import logging
import sys
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants.mca_curriculum import MCA_PROGRAM_METADATA, MCA_SEMESTERS_DATA
from app.models import MCACourse, MCACurriculumScheme, MCAProgram

logger = logging.getLogger("mca_curriculum_seeder")


# ===========================================================================
# Exceptions
# ===========================================================================

class CurriculumSeederError(Exception):
    """Base exception for curriculum seeder failures."""
    pass


class CurriculumSeedMismatchError(CurriculumSeederError):
    """
    Raised when an existing database record conflicts with authoritative
    canonical data, enforcing strict non-destructive safety.
    """
    def __init__(
        self,
        table: str,
        identifier: str,
        field: str,
        expected: Any,
        actual: Any,
    ):
        self.table = table
        self.identifier = identifier
        self.field = field
        self.expected = expected
        self.actual = actual
        message = (
            f"Canonical data mismatch in table '{table}' for record '{identifier}' "
            f"on field '{field}': expected {expected!r}, found {actual!r}. "
            "Seeding aborted and rolled back to prevent silent data corruption."
        )
        super().__init__(message)


# ===========================================================================
# Canonical Specifications
# ===========================================================================

CANONICAL_PROGRAM = {
    "program_name": MCA_PROGRAM_METADATA.get("program_name", "Master of Computer Applications"),
    "program_code": MCA_PROGRAM_METADATA.get("program_code", "MCA"),
    "duration_semesters": int(MCA_PROGRAM_METADATA.get("total_semesters", 4)),
}

CANONICAL_SCHEMES = [
    {
        "scheme_code": "MCA-AUTONOMOUS-2025",
        "scheme_name": "UIT-RGPV Autonomous MCA Scheme (July 2025)",
        "effective_from": "July 2025",
        "effective_until": None,
        "is_active": True,
        "governed_semesters": [1],
        "description": "Official autonomous curriculum scheme effective July 2025 governing Semester 1",
    },
    {
        "scheme_code": "MCA-AUTONOMOUS-2024",
        "scheme_name": "UIT-RGPV Autonomous MCA Scheme (July 2024)",
        "effective_from": "July 2024",
        "effective_until": None,
        "is_active": True,
        "governed_semesters": [3],
        "description": "Official autonomous curriculum scheme effective July 2024 governing Semester 3",
    },
]

# ---------------------------------------------------------------------------
# Authoritative 26 Canonical Courses across 4 Semesters (7 / 7 / 7 / 5)
# Strictly adheres to approved curriculum contract:
# - Allowed course types: 'theory', 'lab', 'elective', 'project'
# - Semesters 1 and 3: Verified codes, credits, and scheme associations
# - Semesters 2 and 4: Provisional (code=None, credits=None, scheme=None)
# ---------------------------------------------------------------------------
CANONICAL_COURSES: List[Dict[str, Any]] = [
    # Semester 1 — Official scheme July 2025 (MCA-AUTONOMOUS-2025)
    {
        "course_code": "MCA108",
        "course_name": "Operating System",
        "semester_number": 1,
        "course_type": "theory",
        "credits": 4,
        "elective_group": None,
        "scheme_code": "MCA-AUTONOMOUS-2025",
    },
    {
        "course_code": "MCA109",
        "course_name": "Programming and Problem Solving in C",
        "semester_number": 1,
        "course_type": "theory",
        "credits": 4,
        "elective_group": None,
        "scheme_code": "MCA-AUTONOMOUS-2025",
    },
    {
        "course_code": "MCA110",
        "course_name": "Mathematical Foundation",
        "semester_number": 1,
        "course_type": "theory",
        "credits": 4,
        "elective_group": None,
        "scheme_code": "MCA-AUTONOMOUS-2025",
    },
    {
        "course_code": "MCA111",
        "course_name": "Fundamentals of Computer Technologies",
        "semester_number": 1,
        "course_type": "theory",
        "credits": 4,
        "elective_group": None,
        "scheme_code": "MCA-AUTONOMOUS-2025",
    },
    {
        "course_code": "MCA112",
        "course_name": "Technical Communication",
        "semester_number": 1,
        "course_type": "theory",
        "credits": 4,
        "elective_group": None,
        "scheme_code": "MCA-AUTONOMOUS-2025",
    },
    {
        "course_code": "MCA113",
        "course_name": "Programming and Problem Solving in C Lab",
        "semester_number": 1,
        "course_type": "lab",
        "credits": 8,
        "elective_group": None,
        "scheme_code": "MCA-AUTONOMOUS-2025",
    },
    {
        "course_code": "MCA114",
        "course_name": "Operating System Lab",
        "semester_number": 1,
        "course_type": "lab",
        "credits": 4,
        "elective_group": None,
        "scheme_code": "MCA-AUTONOMOUS-2025",
    },
    # Semester 2 — Provisional
    {
        "course_code": None,
        "course_name": "Database Management System",
        "semester_number": 2,
        "course_type": "theory",
        "credits": None,
        "elective_group": None,
        "scheme_code": None,
    },
    {
        "course_code": None,
        "course_name": "Computer Network",
        "semester_number": 2,
        "course_type": "theory",
        "credits": None,
        "elective_group": None,
        "scheme_code": None,
    },
    {
        "course_code": None,
        "course_name": "Object Oriented Programming with Java",
        "semester_number": 2,
        "course_type": "theory",
        "credits": None,
        "elective_group": None,
        "scheme_code": None,
    },
    {
        "course_code": None,
        "course_name": "Software Engineering and UML",
        "semester_number": 2,
        "course_type": "theory",
        "credits": None,
        "elective_group": None,
        "scheme_code": None,
    },
    {
        "course_code": None,
        "course_name": "Algorithm Design",
        "semester_number": 2,
        "course_type": "theory",
        "credits": None,
        "elective_group": None,
        "scheme_code": None,
    },
    {
        "course_code": None,
        "course_name": "Java and OOPS Lab",
        "semester_number": 2,
        "course_type": "lab",
        "credits": None,
        "elective_group": None,
        "scheme_code": None,
    },
    {
        "course_code": None,
        "course_name": "DBMS Lab",
        "semester_number": 2,
        "course_type": "lab",
        "credits": None,
        "elective_group": None,
        "scheme_code": None,
    },
    # Semester 3 — Official scheme July 2024 (MCA-AUTONOMOUS-2024)
    {
        "course_code": "MCA301",
        "course_name": "Data Mining",
        "semester_number": 3,
        "course_type": "theory",
        "credits": 4,
        "elective_group": None,
        "scheme_code": "MCA-AUTONOMOUS-2024",
    },
    {
        "course_code": "MCA302",
        "course_name": "Artificial Intelligence",
        "semester_number": 3,
        "course_type": "theory",
        "credits": 4,
        "elective_group": None,
        "scheme_code": "MCA-AUTONOMOUS-2024",
    },
    {
        "course_code": "MCA303",
        "course_name": "Elective-I: Python Programming",
        "semester_number": 3,
        "course_type": "elective",
        "credits": 4,
        "elective_group": "Elective-I",
        "scheme_code": "MCA-AUTONOMOUS-2024",
    },
    {
        "course_code": "MCA304",
        "course_name": "Elective-II: Machine Learning and Deep Learning",
        "semester_number": 3,
        "course_type": "elective",
        "credits": 4,
        "elective_group": "Elective-II",
        "scheme_code": "MCA-AUTONOMOUS-2024",
    },
    {
        "course_code": "MCA305",
        "course_name": "Elective-III: Distributed Systems",
        "semester_number": 3,
        "course_type": "elective",
        "credits": 4,
        "elective_group": "Elective-III",
        "scheme_code": "MCA-AUTONOMOUS-2024",
    },
    {
        "course_code": "MCA306",
        "course_name": "Minor Project",
        "semester_number": 3,
        "course_type": "project",
        "credits": 8,
        "elective_group": None,
        "scheme_code": "MCA-AUTONOMOUS-2024",
    },
    {
        "course_code": "MCA307",
        "course_name": "Elective-I Lab",
        "semester_number": 3,
        "course_type": "lab",
        "credits": 4,
        "elective_group": "Elective-I",
        "scheme_code": "MCA-AUTONOMOUS-2024",
    },
    # Semester 4 — Provisional
    {
        "course_code": None,
        "course_name": "Cloud Computing Technologies",
        "semester_number": 4,
        "course_type": "theory",
        "credits": None,
        "elective_group": None,
        "scheme_code": None,
    },
    {
        "course_code": None,
        "course_name": "Cryptocurrency and Blockchain Technologies",
        "semester_number": 4,
        "course_type": "theory",
        "credits": None,
        "elective_group": None,
        "scheme_code": None,
    },
    {
        "course_code": None,
        "course_name": "Advanced Python",
        "semester_number": 4,
        "course_type": "theory",
        "credits": None,
        "elective_group": None,
        "scheme_code": None,
    },
    {
        "course_code": None,
        "course_name": "Information Security",
        "semester_number": 4,
        "course_type": "theory",
        "credits": None,
        "elective_group": None,
        "scheme_code": None,
    },
    {
        "course_code": None,
        "course_name": "Big Data Analytics",
        "semester_number": 4,
        "course_type": "theory",
        "credits": None,
        "elective_group": None,
        "scheme_code": None,
    },
]


# ===========================================================================
# Seeder Helpers
# ===========================================================================

def _seed_program(session: Session) -> Tuple[MCAProgram, str]:
    """
    Seed or verify the canonical MCA program.
    Returns (program_entity, action) where action is 'INSERTED' or 'UNCHANGED'.
    """
    code = CANONICAL_PROGRAM["program_code"]
    existing: Optional[MCAProgram] = session.execute(
        select(MCAProgram).where(MCAProgram.program_code == code)
    ).scalar_one_or_none()

    if existing is None:
        program = MCAProgram(
            program_name=CANONICAL_PROGRAM["program_name"],
            program_code=code,
            duration_semesters=CANONICAL_PROGRAM["duration_semesters"],
        )
        session.add(program)
        session.flush()
        logger.info(f"Inserted canonical program: {code} (id={program.id})")
        return program, "INSERTED"

    # Mismatch detection on existing program
    if existing.program_name != CANONICAL_PROGRAM["program_name"]:
        raise CurriculumSeedMismatchError(
            table="mca_programs",
            identifier=f"program_code={code}",
            field="program_name",
            expected=CANONICAL_PROGRAM["program_name"],
            actual=existing.program_name,
        )
    if existing.duration_semesters != CANONICAL_PROGRAM["duration_semesters"]:
        raise CurriculumSeedMismatchError(
            table="mca_programs",
            identifier=f"program_code={code}",
            field="duration_semesters",
            expected=CANONICAL_PROGRAM["duration_semesters"],
            actual=existing.duration_semesters,
        )

    logger.info(f"Verified existing matching canonical program: {code} (id={existing.id})")
    return existing, "UNCHANGED"


def _seed_schemes(
    session: Session,
    program: MCAProgram,
) -> Tuple[Dict[str, MCACurriculumScheme], int, int]:
    """
    Seed or verify the two officially verified curriculum schemes.
    Returns (schemes_by_code, inserted_count, unchanged_count).
    """
    schemes_by_code: Dict[str, MCACurriculumScheme] = {}
    inserted = 0
    unchanged = 0

    for spec in CANONICAL_SCHEMES:
        code = spec["scheme_code"]
        existing: Optional[MCACurriculumScheme] = session.execute(
            select(MCACurriculumScheme).where(MCACurriculumScheme.scheme_code == code)
        ).scalar_one_or_none()

        if existing is None:
            scheme = MCACurriculumScheme(
                program_id=program.id,
                scheme_name=spec["scheme_name"],
                scheme_code=code,
                effective_from=spec["effective_from"],
                effective_until=spec["effective_until"],
                is_active=spec["is_active"],
            )
            session.add(scheme)
            session.flush()
            schemes_by_code[code] = scheme
            inserted += 1
            logger.info(f"Inserted canonical scheme: {code} (id={scheme.id})")
            continue

        # Mismatch detection on existing scheme
        if existing.program_id != program.id:
            raise CurriculumSeedMismatchError(
                table="mca_curriculum_schemes",
                identifier=f"scheme_code={code}",
                field="program_id",
                expected=program.id,
                actual=existing.program_id,
            )
        if existing.scheme_name != spec["scheme_name"]:
            raise CurriculumSeedMismatchError(
                table="mca_curriculum_schemes",
                identifier=f"scheme_code={code}",
                field="scheme_name",
                expected=spec["scheme_name"],
                actual=existing.scheme_name,
            )
        if existing.effective_from != spec["effective_from"]:
            raise CurriculumSeedMismatchError(
                table="mca_curriculum_schemes",
                identifier=f"scheme_code={code}",
                field="effective_from",
                expected=spec["effective_from"],
                actual=existing.effective_from,
            )
        if existing.effective_until != spec["effective_until"]:
            raise CurriculumSeedMismatchError(
                table="mca_curriculum_schemes",
                identifier=f"scheme_code={code}",
                field="effective_until",
                expected=spec["effective_until"],
                actual=existing.effective_until,
            )
        if existing.is_active != spec["is_active"]:
            raise CurriculumSeedMismatchError(
                table="mca_curriculum_schemes",
                identifier=f"scheme_code={code}",
                field="is_active",
                expected=spec["is_active"],
                actual=existing.is_active,
            )

        schemes_by_code[code] = existing
        unchanged += 1
        logger.info(f"Verified existing matching canonical scheme: {code} (id={existing.id})")

    return schemes_by_code, inserted, unchanged


def _seed_courses(
    session: Session,
    program: MCAProgram,
    schemes_by_code: Dict[str, MCACurriculumScheme],
) -> Tuple[int, int, Dict[int, int]]:
    """
    Seed or verify all 26 canonical courses across 4 semesters.
    Returns (inserted_count, unchanged_count, semester_counts).
    """
    inserted = 0
    unchanged = 0
    semester_counts: Dict[int, int] = {1: 0, 2: 0, 3: 0, 4: 0}

    for course_spec in CANONICAL_COURSES:
        c_code = course_spec["course_code"]
        c_name = course_spec["course_name"]
        sem_num = int(course_spec["semester_number"])
        c_type = course_spec["course_type"]
        c_credits = course_spec["credits"]
        c_elective = course_spec["elective_group"]
        scheme_code = course_spec["scheme_code"]

        expected_scheme_id = schemes_by_code[scheme_code].id if scheme_code else None

        # Look up existing course
        existing: Optional[MCACourse] = None
        if c_code is not None:
            # Verified courses: lookup by (program_id, course_code)
            existing = session.execute(
                select(MCACourse).where(
                    MCACourse.program_id == program.id,
                    MCACourse.course_code == c_code,
                )
            ).scalar_one_or_none()
        else:
            # Provisional courses (c_code is None): lookup by (program_id, semester_number, course_name)
            existing = session.execute(
                select(MCACourse).where(
                    MCACourse.program_id == program.id,
                    MCACourse.semester_number == sem_num,
                    MCACourse.course_name == c_name,
                )
            ).scalar_one_or_none()

        # Also check if existing course with same name exists under this program/semester to catch mismatch
        if existing is None and c_code is not None:
            by_name = session.execute(
                select(MCACourse).where(
                    MCACourse.program_id == program.id,
                    MCACourse.semester_number == sem_num,
                    MCACourse.course_name == c_name,
                )
            ).scalar_one_or_none()
            if by_name is not None:
                # Name matches but code differs: explicit mismatch
                raise CurriculumSeedMismatchError(
                    table="mca_courses",
                    identifier=f"{c_name} (Sem {sem_num})",
                    field="course_code",
                    expected=c_code,
                    actual=by_name.course_code,
                )

        if existing is None:
            course = MCACourse(
                program_id=program.id,
                scheme_id=expected_scheme_id,
                course_code=c_code,
                course_name=c_name,
                semester_number=sem_num,
                course_type=c_type,
                elective_group=c_elective,
                credits=c_credits,
            )
            session.add(course)
            session.flush()
            inserted += 1
            semester_counts[sem_num] += 1
            logger.info(f"Inserted course: [{c_code or 'PROVISIONAL'}] {c_name} (Sem {sem_num})")
            continue

        # Mismatch verification on existing course
        identifier = f"{c_name} (code={c_code or 'None'}, sem={sem_num})"

        if existing.course_name != c_name:
            raise CurriculumSeedMismatchError(
                table="mca_courses",
                identifier=identifier,
                field="course_name",
                expected=c_name,
                actual=existing.course_name,
            )
        if existing.course_code != c_code:
            raise CurriculumSeedMismatchError(
                table="mca_courses",
                identifier=identifier,
                field="course_code",
                expected=c_code,
                actual=existing.course_code,
            )
        if existing.semester_number != sem_num:
            raise CurriculumSeedMismatchError(
                table="mca_courses",
                identifier=identifier,
                field="semester_number",
                expected=sem_num,
                actual=existing.semester_number,
            )
        if existing.course_type != c_type:
            raise CurriculumSeedMismatchError(
                table="mca_courses",
                identifier=identifier,
                field="course_type",
                expected=c_type,
                actual=existing.course_type,
            )
        if existing.elective_group != c_elective:
            raise CurriculumSeedMismatchError(
                table="mca_courses",
                identifier=identifier,
                field="elective_group",
                expected=c_elective,
                actual=existing.elective_group,
            )
        if existing.credits != c_credits:
            raise CurriculumSeedMismatchError(
                table="mca_courses",
                identifier=identifier,
                field="credits",
                expected=c_credits,
                actual=existing.credits,
            )
        if existing.scheme_id != expected_scheme_id:
            raise CurriculumSeedMismatchError(
                table="mca_courses",
                identifier=identifier,
                field="scheme_id",
                expected=expected_scheme_id,
                actual=existing.scheme_id,
            )

        unchanged += 1
        semester_counts[sem_num] += 1
        logger.info(f"Verified existing matching course: [{c_code or 'PROVISIONAL'}] {c_name} (Sem {sem_num})")

    return inserted, unchanged, semester_counts

    return inserted, unchanged, semester_counts


# ===========================================================================
# Primary Seeding Function
# ===========================================================================

def seed_mca_curriculum(session: Session, commit: bool = True) -> Dict[str, Any]:
    """
    Execute the canonical MCA curriculum seeder within the provided SQLAlchemy session.

    Args:
        session: Active SQLAlchemy Session.
        commit: If True, commits the transaction upon successful validation.
                If False, flushes but does not commit (useful for dry-run or testing).

    Returns:
        Structured result dictionary detailing actions taken.

    Raises:
        CurriculumSeedMismatchError: If any existing record conflicts with canonical data.
        CurriculumSeederError: On any other database or configuration error.
    """
    try:
        # 1. Seed or verify Program
        program, prog_action = _seed_program(session)

        # 2. Seed or verify Schemes
        schemes_by_code, schemes_inserted, schemes_unchanged = _seed_schemes(session, program)

        # 3. Seed or verify Courses
        courses_inserted, courses_unchanged, semester_counts = _seed_courses(
            session, program, schemes_by_code
        )

        total_courses = courses_inserted + courses_unchanged

        # Sanity check total course count and distribution
        if total_courses != 26:
            raise CurriculumSeederError(
                f"Unexpected total course count after seeding: expected 26, got {total_courses}"
            )
        expected_dist = {1: 7, 2: 7, 3: 7, 4: 5}
        if semester_counts != expected_dist:
            raise CurriculumSeederError(
                f"Unexpected semester course distribution: expected {expected_dist}, got {semester_counts}"
            )

        if commit:
            session.commit()
            logger.info("Canonical MCA curriculum seeder committed successfully.")
        else:
            session.flush()
            logger.info("Canonical MCA curriculum seeder completed flush (commit=False).")

        return {
            "status": "SUCCESS",
            "program": {
                "id": program.id,
                "code": program.program_code,
                "name": program.program_name,
                "action": prog_action,
            },
            "schemes": {
                "inserted": schemes_inserted,
                "unchanged": schemes_unchanged,
                "codes": list(schemes_by_code.keys()),
            },
            "courses": {
                "inserted": courses_inserted,
                "unchanged": courses_unchanged,
                "total": total_courses,
                "by_semester": semester_counts,
            },
        }

    except Exception as exc:
        session.rollback()
        logger.error(f"Seeder aborted with rollback: {exc}")
        raise


# ===========================================================================
# CLI Entry Point
# ===========================================================================

def main() -> None:
    """CLI entry point for manual seeder invocation."""
    parser = argparse.ArgumentParser(
        description="Canonical MCA Curriculum Seeder (UIT-RGPV Autonomous)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Execute in dry-run mode (rolls back all changes without committing).",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose DEBUG logging.",
    )

    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    # Import SessionLocal from application database configuration
    from app.database import SessionLocal

    session: Session = SessionLocal()
    try:
        commit_changes = not args.dry_run
        result = seed_mca_curriculum(session, commit=commit_changes)
        if args.dry_run:
            session.rollback()
            print("\n[DRY RUN COMPLETE] Transaction rolled back safely. Proposed result:")
        else:
            print("\n[SEEDING COMPLETE] Successfully committed canonical curriculum:")

        print(f"  Program : {result['program']['code']} ({result['program']['action']})")
        print(f"  Schemes : {result['schemes']['inserted']} inserted, {result['schemes']['unchanged']} unchanged")
        print(f"  Courses : {result['courses']['inserted']} inserted, {result['courses']['unchanged']} unchanged")
        print(f"  Distribution: {result['courses']['by_semester']}")
        sys.exit(0)

    except CurriculumSeedMismatchError as err:
        print(f"\n[CANONICAL MISMATCH ERROR] {err}", file=sys.stderr)
        sys.exit(2)
    except Exception as err:
        print(f"\n[SEEDER FATAL ERROR] {err}", file=sys.stderr)
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    main()
