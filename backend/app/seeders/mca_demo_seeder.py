"""
backend/app/seeders/mca_demo_seeder.py

Safe, Idempotent Demonstration Data Seeder for MCA Academic Performance System.
Populates realistic demonstration cohort data for end-to-end evaluation.

Adheres strictly to Phase 4.5 Specifications and Phase 2B Implementation Contract:
1. Never creates or modifies canonical courses, schemes, or the MCA program.
   Aborts immediately with DemoSeederError if canonical prerequisites are missing.
2. Every demonstration entity carries an explicit 'DEMO-' prefixed identifier:
   - Academic Session: DEMO-MCA-2025-27-COHORT
   - Student A: DEMO-MCA-2025-001 (Strong Academic Profile)
   - Student B: DEMO-MCA-2025-002 (At-Risk Academic Profile)
3. Does NOT alter schema or introduce synthetic/is_demo columns.
4. Read-before-insert idempotency: checks existence before inserting.
5. Strict non-destructive guarantee: never overwrites or deletes existing records;
   raises DemoSeederMismatchError if existing attributes differ.
6. Atomic transaction: single transaction with full rollback on any error.
7. Realistic point-in-time snapshots with valid chronological timestamps.
8. No official semester results claimed (students are in active 1st semester).
"""

from datetime import date, datetime, timezone
from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    MCAAcademicSession,
    MCAAttendanceSnapshot,
    MCACourse,
    MCACourseRegistration,
    MCACurriculumScheme,
    MCAFormativeSnapshot,
    MCAProgram,
    MCASessionCourse,
    MCAStudent,
)

logger = logging.getLogger("mca_demo_seeder")


# ===========================================================================
# Custom Exceptions
# ===========================================================================

class DemoSeederError(Exception):
    """Base exception for demonstration data seeder failures."""
    pass


class DemoSeederPrerequisiteError(DemoSeederError):
    """Raised when canonical prerequisites (program, scheme, courses) are missing."""
    pass


class DemoSeederMismatchError(DemoSeederError):
    """
    Raised when an existing record differs from the expected demonstration specification.
    Aborts seeding immediately with rollback to protect database integrity.
    """
    def __init__(self, table: str, identifier: str, field: str, expected: Any, actual: Any):
        self.table = table
        self.identifier = identifier
        self.field = field
        self.expected = expected
        self.actual = actual
        message = (
            f"Demonstration data mismatch in table '{table}' for record '{identifier}' "
            f"on field '{field}': expected {expected!r}, found {actual!r}. "
            "Seeding aborted and rolled back to prevent silent state corruption."
        )
        super().__init__(message)


# ===========================================================================
# Demonstration Specifications
# ===========================================================================

DEMO_PROGRAM_CODE = "MCA"
DEMO_SCHEME_CODE = "MCA-AUTONOMOUS-2025"

DEMO_COURSE_CODES = ["MCA108", "MCA109", "MCA113", "MCA114"]

DEMO_SESSION_SPEC = {
    "session_name": "DEMO-MCA-2025-27-COHORT",
    "batch_year": "2025-2027 (DEMO)",
    "start_date": date(2025, 7, 1),
    "end_date": date(2027, 6, 30),
    "is_active": True,
}

DEMO_STUDENTS_SPEC = [
    {
        "student_code": "DEMO-MCA-2025-001",
        "description": "Student A (Strong Profile - High Attendance, Strong Formatives)",
    },
    {
        "student_code": "DEMO-MCA-2025-002",
        "description": "Student B (At-Risk Profile - Low Attendance, Weak Formatives)",
    },
]

DEMO_REGISTRATION_DATE = datetime(2025, 7, 15, 9, 0, 0, tzinfo=timezone.utc)

# Attendance Snapshot Chronology
ATT_REV1_TIMESTAMP = datetime(2025, 8, 15, 10, 0, 0, tzinfo=timezone.utc)
ATT_REV2_TIMESTAMP = datetime(2025, 9, 15, 10, 0, 0, tzinfo=timezone.utc)

DEMO_ATTENDANCE_SPEC = {
    "DEMO-MCA-2025-001": [
        {
            "revision_number": 1,
            "recorded_at": ATT_REV1_TIMESTAMP,
            "attendance_percentage": Decimal("88.00"),
            "classes_held": 25,
            "classes_attended": 22,
        },
        {
            "revision_number": 2,
            "recorded_at": ATT_REV2_TIMESTAMP,
            "attendance_percentage": Decimal("92.00"),
            "classes_held": 50,
            "classes_attended": 46,
        },
    ],
    "DEMO-MCA-2025-002": [
        {
            "revision_number": 1,
            "recorded_at": ATT_REV1_TIMESTAMP,
            "attendance_percentage": Decimal("64.00"),
            "classes_held": 25,
            "classes_attended": 16,
        },
        {
            "revision_number": 2,
            "recorded_at": ATT_REV2_TIMESTAMP,
            "attendance_percentage": Decimal("58.00"),
            "classes_held": 50,
            "classes_attended": 29,
        },
    ],
}

# Formative Snapshot Chronology
FORM_REV1_TIMESTAMP = datetime(2025, 9, 10, 14, 0, 0, tzinfo=timezone.utc)

DEMO_FORMATIVE_SPEC = {
    "DEMO-MCA-2025-001": {
        # Theory courses
        "MCA108": {
            "revision_number": 1,
            "recorded_at": FORM_REV1_TIMESTAMP,
            "mst1_marks": Decimal("18.00"),
            "mst2_marks": None,
            "assignment_score": Decimal("9.50"),
            "viva_marks": None,
            "lab_record_score": None,
        },
        "MCA109": {
            "revision_number": 1,
            "recorded_at": FORM_REV1_TIMESTAMP,
            "mst1_marks": Decimal("18.00"),
            "mst2_marks": None,
            "assignment_score": Decimal("9.50"),
            "viva_marks": None,
            "lab_record_score": None,
        },
        # Lab courses
        "MCA113": {
            "revision_number": 1,
            "recorded_at": FORM_REV1_TIMESTAMP,
            "mst1_marks": Decimal("17.00"),
            "mst2_marks": None,
            "assignment_score": Decimal("9.00"),
            "viva_marks": Decimal("8.50"),
            "lab_record_score": Decimal("9.00"),
        },
        "MCA114": {
            "revision_number": 1,
            "recorded_at": FORM_REV1_TIMESTAMP,
            "mst1_marks": Decimal("17.00"),
            "mst2_marks": None,
            "assignment_score": Decimal("9.00"),
            "viva_marks": Decimal("8.50"),
            "lab_record_score": Decimal("9.00"),
        },
    },
    "DEMO-MCA-2025-002": {
        # Theory courses
        "MCA108": {
            "revision_number": 1,
            "recorded_at": FORM_REV1_TIMESTAMP,
            "mst1_marks": Decimal("9.00"),
            "mst2_marks": None,
            "assignment_score": Decimal("5.00"),
            "viva_marks": None,
            "lab_record_score": None,
        },
        "MCA109": {
            "revision_number": 1,
            "recorded_at": FORM_REV1_TIMESTAMP,
            "mst1_marks": Decimal("9.00"),
            "mst2_marks": None,
            "assignment_score": Decimal("5.00"),
            "viva_marks": None,
            "lab_record_score": None,
        },
        # Lab courses
        "MCA113": {
            "revision_number": 1,
            "recorded_at": FORM_REV1_TIMESTAMP,
            "mst1_marks": Decimal("8.00"),
            "mst2_marks": None,
            "assignment_score": Decimal("5.00"),
            "viva_marks": Decimal("4.00"),
            "lab_record_score": Decimal("5.50"),
        },
        "MCA114": {
            "revision_number": 1,
            "recorded_at": FORM_REV1_TIMESTAMP,
            "mst1_marks": Decimal("8.00"),
            "mst2_marks": None,
            "assignment_score": Decimal("5.00"),
            "viva_marks": Decimal("4.00"),
            "lab_record_score": Decimal("5.50"),
        },
    },
}


# ===========================================================================
# Numeric Comparison Helper
# ===========================================================================

def _numeric_matches(actual: Any, expected: Optional[Decimal]) -> bool:
    """Safe comparison of Decimal/Float/Numeric values handling None."""
    if actual is None and expected is None:
        return True
    if actual is None or expected is None:
        return False
    return round(float(actual), 2) == round(float(expected), 2)


# ===========================================================================
# Demonstration Seeder Execution
# ===========================================================================

def seed_mca_demonstration_data(session: Session) -> Dict[str, Any]:
    """
    Seed illustrative demonstration cohort data in an atomic transaction.

    Verification Steps:
    1. Verify canonical MCA program and MCA-AUTONOMOUS-2025 scheme exist.
    2. Verify canonical courses MCA108, MCA109, MCA113, MCA114 exist.
    3. Idempotently create/verify DEMO-MCA-2025-27-COHORT academic session.
    4. Idempotently create/verify session-course offerings for the 4 courses.
    5. Idempotently create/verify DEMO-MCA-2025-001 and DEMO-MCA-2025-002 students.
    6. Idempotently create/verify 8 course registrations (regular, sem 1).
    7. Idempotently create/verify 16 attendance snapshots (2 revisions per reg).
    8. Idempotently create/verify 8 formative snapshots (1 revision per reg).

    Returns:
        Structured dictionary reporting counts of created vs existing records.
    """
    stats = {
        "session": {"created": False, "id": None, "session_name": DEMO_SESSION_SPEC["session_name"]},
        "session_courses": {"created": 0, "total": 0},
        "students": {"created": 0, "total": 0, "student_codes": []},
        "registrations": {"created": 0, "total": 0},
        "attendance_snapshots": {"created": 0, "total": 0},
        "formative_snapshots": {"created": 0, "total": 0},
    }

    try:
        # -------------------------------------------------------------------
        # Step 1: Verify Canonical Prerequisites
        # -------------------------------------------------------------------
        program = session.execute(
            select(MCAProgram).where(MCAProgram.program_code == DEMO_PROGRAM_CODE)
        ).scalar_one_or_none()
        if program is None:
            raise DemoSeederPrerequisiteError(
                f"Canonical MCA program '{DEMO_PROGRAM_CODE}' not found in database. "
                "Please run mca_curriculum_seeder before seeding demonstration data."
            )

        scheme = session.execute(
            select(MCACurriculumScheme).where(MCACurriculumScheme.scheme_code == DEMO_SCHEME_CODE)
        ).scalar_one_or_none()
        if scheme is None:
            raise DemoSeederPrerequisiteError(
                f"Canonical curriculum scheme '{DEMO_SCHEME_CODE}' not found in database. "
                "Please run mca_curriculum_seeder before seeding demonstration data."
            )

        # Check canonical courses
        course_map: Dict[str, MCACourse] = {}
        for code in DEMO_COURSE_CODES:
            course = session.execute(
                select(MCACourse).where(
                    MCACourse.program_id == program.id,
                    MCACourse.course_code == code,
                )
            ).scalar_one_or_none()
            if course is None:
                raise DemoSeederPrerequisiteError(
                    f"Canonical course '{code}' not found for program '{DEMO_PROGRAM_CODE}'. "
                    "Please run mca_curriculum_seeder before seeding demonstration data."
                )
            course_map[code] = course

        logger.info("Canonical prerequisites verified successfully.")

        # -------------------------------------------------------------------
        # Step 2: Demonstration Academic Session
        # -------------------------------------------------------------------
        demo_session_name = DEMO_SESSION_SPEC["session_name"]
        db_session_obj = session.execute(
            select(MCAAcademicSession).where(MCAAcademicSession.session_name == demo_session_name)
        ).scalar_one_or_none()

        if db_session_obj is None:
            db_session_obj = MCAAcademicSession(
                scheme_id=scheme.id,
                session_name=demo_session_name,
                batch_year=DEMO_SESSION_SPEC["batch_year"],
                start_date=DEMO_SESSION_SPEC["start_date"],
                end_date=DEMO_SESSION_SPEC["end_date"],
                is_active=DEMO_SESSION_SPEC["is_active"],
            )
            session.add(db_session_obj)
            session.flush()
            stats["session"]["created"] = True
            logger.info("Created demonstration academic session: %s (id=%d)", demo_session_name, db_session_obj.id)
        else:
            # Verify attributes match
            if db_session_obj.scheme_id != scheme.id:
                raise DemoSeederMismatchError(
                    "mca_academic_sessions", demo_session_name, "scheme_id", scheme.id, db_session_obj.scheme_id
                )
            if db_session_obj.batch_year != DEMO_SESSION_SPEC["batch_year"]:
                raise DemoSeederMismatchError(
                    "mca_academic_sessions", demo_session_name, "batch_year", DEMO_SESSION_SPEC["batch_year"], db_session_obj.batch_year
                )
            if db_session_obj.start_date != DEMO_SESSION_SPEC["start_date"]:
                raise DemoSeederMismatchError(
                    "mca_academic_sessions", demo_session_name, "start_date", DEMO_SESSION_SPEC["start_date"], db_session_obj.start_date
                )
            if db_session_obj.end_date != DEMO_SESSION_SPEC["end_date"]:
                raise DemoSeederMismatchError(
                    "mca_academic_sessions", demo_session_name, "end_date", DEMO_SESSION_SPEC["end_date"], db_session_obj.end_date
                )
            if db_session_obj.is_active != DEMO_SESSION_SPEC["is_active"]:
                raise DemoSeederMismatchError(
                    "mca_academic_sessions", demo_session_name, "is_active", DEMO_SESSION_SPEC["is_active"], db_session_obj.is_active
                )
            logger.info("Verified existing demonstration academic session: %s (id=%d)", demo_session_name, db_session_obj.id)

        stats["session"]["id"] = db_session_obj.id

        # -------------------------------------------------------------------
        # Step 3: Session-Course Mappings
        # -------------------------------------------------------------------
        session_course_map: Dict[str, MCASessionCourse] = {}
        for code in DEMO_COURSE_CODES:
            course = course_map[code]
            sc = session.execute(
                select(MCASessionCourse).where(
                    MCASessionCourse.session_id == db_session_obj.id,
                    MCASessionCourse.course_id == course.id,
                )
            ).scalar_one_or_none()

            if sc is None:
                sc = MCASessionCourse(
                    session_id=db_session_obj.id,
                    course_id=course.id,
                )
                session.add(sc)
                session.flush()
                stats["session_courses"]["created"] += 1
                logger.info("Created session course: session=%d, course=%s (id=%d)", db_session_obj.id, code, sc.id)

            session_course_map[code] = sc
            stats["session_courses"]["total"] += 1

        # -------------------------------------------------------------------
        # Step 4: Demonstration Students
        # -------------------------------------------------------------------
        student_obj_map: Dict[str, MCAStudent] = {}
        for s_spec in DEMO_STUDENTS_SPEC:
            s_code = s_spec["student_code"]
            student = session.execute(
                select(MCAStudent).where(MCAStudent.student_code == s_code)
            ).scalar_one_or_none()

            if student is None:
                student = MCAStudent(
                    student_code=s_code,
                    session_id=db_session_obj.id,
                    is_active=True,
                    deactivated_at=None,
                    deactivation_reason=None,
                )
                session.add(student)
                session.flush()
                stats["students"]["created"] += 1
                logger.info("Created demonstration student: %s (id=%d)", s_code, student.id)
            else:
                if student.session_id != db_session_obj.id:
                    raise DemoSeederMismatchError(
                        "mca_students", s_code, "session_id", db_session_obj.id, student.session_id
                    )
                if not student.is_active:
                    raise DemoSeederMismatchError(
                        "mca_students", s_code, "is_active", True, student.is_active
                    )
                logger.info("Verified existing demonstration student: %s (id=%d)", s_code, student.id)

            student_obj_map[s_code] = student
            stats["students"]["student_codes"].append(s_code)
            stats["students"]["total"] += 1

        # -------------------------------------------------------------------
        # Step 5: Course Registrations (8 total)
        # -------------------------------------------------------------------
        # Mapping: (student_code, course_code) -> MCACourseRegistration
        reg_map: Dict[tuple[str, str], MCACourseRegistration] = {}

        for s_code, student in student_obj_map.items():
            for c_code, sc in session_course_map.items():
                reg = session.execute(
                    select(MCACourseRegistration).where(
                        MCACourseRegistration.student_id == student.id,
                        MCACourseRegistration.session_course_id == sc.id,
                    )
                ).scalar_one_or_none()

                if reg is None:
                    reg = MCACourseRegistration(
                        student_id=student.id,
                        session_course_id=sc.id,
                        semester_number=1,
                        attempt_type="regular",
                        is_active=True,
                        registered_at=DEMO_REGISTRATION_DATE,
                    )
                    session.add(reg)
                    session.flush()
                    stats["registrations"]["created"] += 1
                    logger.info("Created registration: student=%s, course=%s (id=%d)", s_code, c_code, reg.id)
                else:
                    if reg.semester_number != 1:
                        raise DemoSeederMismatchError(
                            "mca_course_registrations", f"reg_s{student.id}_c{sc.id}", "semester_number", 1, reg.semester_number
                        )
                    if reg.attempt_type != "regular":
                        raise DemoSeederMismatchError(
                            "mca_course_registrations", f"reg_s{student.id}_c{sc.id}", "attempt_type", "regular", reg.attempt_type
                        )
                    if not reg.is_active:
                        raise DemoSeederMismatchError(
                            "mca_course_registrations", f"reg_s{student.id}_c{sc.id}", "is_active", True, reg.is_active
                        )
                    logger.info("Verified existing registration: student=%s, course=%s (id=%d)", s_code, c_code, reg.id)

                reg_map[(s_code, c_code)] = reg
                stats["registrations"]["total"] += 1

        # -------------------------------------------------------------------
        # Step 6: Attendance Snapshots (16 total: 2 revisions * 8 registrations)
        # -------------------------------------------------------------------
        for s_code, att_snapshots in DEMO_ATTENDANCE_SPEC.items():
            for c_code in DEMO_COURSE_CODES:
                reg = reg_map[(s_code, c_code)]
                for snap_spec in att_snapshots:
                    rev_num = snap_spec["revision_number"]
                    att_snap = session.execute(
                        select(MCAAttendanceSnapshot).where(
                            MCAAttendanceSnapshot.registration_id == reg.id,
                            MCAAttendanceSnapshot.revision_number == rev_num,
                        )
                    ).scalar_one_or_none()

                    if att_snap is None:
                        att_snap = MCAAttendanceSnapshot(
                            registration_id=reg.id,
                            revision_number=rev_num,
                            recorded_at=snap_spec["recorded_at"],
                            attendance_percentage=snap_spec["attendance_percentage"],
                            classes_held=snap_spec["classes_held"],
                            classes_attended=snap_spec["classes_attended"],
                        )
                        session.add(att_snap)
                        session.flush()
                        stats["attendance_snapshots"]["created"] += 1
                    else:
                        if not _numeric_matches(att_snap.attendance_percentage, snap_spec["attendance_percentage"]):
                            raise DemoSeederMismatchError(
                                "mca_attendance_snapshots",
                                f"reg_{reg.id}_rev_{rev_num}",
                                "attendance_percentage",
                                snap_spec["attendance_percentage"],
                                att_snap.attendance_percentage,
                            )
                        if att_snap.classes_held != snap_spec["classes_held"]:
                            raise DemoSeederMismatchError(
                                "mca_attendance_snapshots",
                                f"reg_{reg.id}_rev_{rev_num}",
                                "classes_held",
                                snap_spec["classes_held"],
                                att_snap.classes_held,
                            )
                        if att_snap.classes_attended != snap_spec["classes_attended"]:
                            raise DemoSeederMismatchError(
                                "mca_attendance_snapshots",
                                f"reg_{reg.id}_rev_{rev_num}",
                                "classes_attended",
                                snap_spec["classes_attended"],
                                att_snap.classes_attended,
                            )

                    stats["attendance_snapshots"]["total"] += 1

        # -------------------------------------------------------------------
        # Step 7: Formative Assessment Snapshots (8 total: 1 per registration)
        # -------------------------------------------------------------------
        for s_code, course_formatives in DEMO_FORMATIVE_SPEC.items():
            for c_code, form_spec in course_formatives.items():
                reg = reg_map[(s_code, c_code)]
                rev_num = form_spec["revision_number"]
                form_snap = session.execute(
                    select(MCAFormativeSnapshot).where(
                        MCAFormativeSnapshot.registration_id == reg.id,
                        MCAFormativeSnapshot.revision_number == rev_num,
                    )
                ).scalar_one_or_none()

                if form_snap is None:
                    form_snap = MCAFormativeSnapshot(
                        registration_id=reg.id,
                        revision_number=rev_num,
                        recorded_at=form_spec["recorded_at"],
                        mst1_marks=form_spec["mst1_marks"],
                        mst2_marks=form_spec["mst2_marks"],
                        assignment_score=form_spec["assignment_score"],
                        viva_marks=form_spec["viva_marks"],
                        lab_record_score=form_spec["lab_record_score"],
                    )
                    session.add(form_snap)
                    session.flush()
                    stats["formative_snapshots"]["created"] += 1
                else:
                    if not _numeric_matches(form_snap.mst1_marks, form_spec["mst1_marks"]):
                        raise DemoSeederMismatchError(
                            "mca_formative_snapshots",
                            f"reg_{reg.id}_rev_{rev_num}",
                            "mst1_marks",
                            form_spec["mst1_marks"],
                            form_snap.mst1_marks,
                        )
                    if not _numeric_matches(form_snap.assignment_score, form_spec["assignment_score"]):
                        raise DemoSeederMismatchError(
                            "mca_formative_snapshots",
                            f"reg_{reg.id}_rev_{rev_num}",
                            "assignment_score",
                            form_spec["assignment_score"],
                            form_snap.assignment_score,
                        )
                    if not _numeric_matches(form_snap.viva_marks, form_spec["viva_marks"]):
                        raise DemoSeederMismatchError(
                            "mca_formative_snapshots",
                            f"reg_{reg.id}_rev_{rev_num}",
                            "viva_marks",
                            form_spec["viva_marks"],
                            form_snap.viva_marks,
                        )
                    if not _numeric_matches(form_snap.lab_record_score, form_spec["lab_record_score"]):
                        raise DemoSeederMismatchError(
                            "mca_formative_snapshots",
                            f"reg_{reg.id}_rev_{rev_num}",
                            "lab_record_score",
                            form_spec["lab_record_score"],
                            form_snap.lab_record_score,
                        )

                stats["formative_snapshots"]["total"] += 1

        # Commit single atomic transaction
        session.commit()
        logger.info("Demonstration data seeding transaction committed successfully.")
        return stats

    except Exception as exc:
        session.rollback()
        logger.error("Demonstration data seeding failed and was rolled back: %s", exc)
        raise


# ===========================================================================
# CLI Execution Entry Point
# ===========================================================================

def main():
    """CLI execution for demonstration data seeder."""
    import argparse
    import sys
    from app.database import SessionLocal

    parser = argparse.ArgumentParser(
        description="Seed demonstration cohort data for MCA Performance System."
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose DEBUG logging.",
    )

    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    session: Session = SessionLocal()
    try:
        stats = seed_mca_demonstration_data(session)
        print("\n[SEEDING COMPLETE] Successfully seeded MCA demonstration data:")
        print(f"  Session             : {stats['session']['session_name']} (created={stats['session']['created']}, id={stats['session']['id']})")
        print(f"  Session Courses     : {stats['session_courses']['created']} created / {stats['session_courses']['total']} total")
        print(f"  Students            : {stats['students']['created']} created / {stats['students']['total']} total ({', '.join(stats['students']['student_codes'])})")
        print(f"  Registrations       : {stats['registrations']['created']} created / {stats['registrations']['total']} total")
        print(f"  Attendance Snaps    : {stats['attendance_snapshots']['created']} created / {stats['attendance_snapshots']['total']} total")
        print(f"  Formative Snaps     : {stats['formative_snapshots']['created']} created / {stats['formative_snapshots']['total']} total")
        sys.exit(0)
    except DemoSeederMismatchError as err:
        print(f"\n[DEMO SEEDER MISMATCH ERROR] {err}", file=sys.stderr)
        sys.exit(2)
    except DemoSeederPrerequisiteError as err:
        print(f"\n[DEMO PREREQUISITE ERROR] {err}", file=sys.stderr)
        sys.exit(3)
    except Exception as err:
        print(f"\n[DEMO SEEDER FATAL ERROR] {err}", file=sys.stderr)
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    main()
