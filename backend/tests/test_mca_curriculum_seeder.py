"""
backend/tests/test_mca_curriculum_seeder.py

Automated test suite for Phase 2D: Canonical MCA Curriculum Seeder.
Verifies:
1. Exactly 26 courses exist.
2. Semester distribution is 7 / 7 / 7 / 5.
3. Every course title exactly matches the authoritative list.
4. Every course has the correct semester and course type (theory, lab, elective, project).
5. All 14 verified codes and credits match the approved catalogue.
6. Semester 2 and 4 codes, credits and scheme associations are NULL.
7. Only Semesters 1 and 3 are associated with their respective verified schemes.
8. Repeated seeding creates no duplicates.
9. Matching records remain unchanged.
10. Conflicting records trigger rollback.
11. No academic sessions, mappings, students, registrations, snapshots or prediction records are created.
12. Phase 1 UCI infrastructure remains unaffected.

Strict isolation:
- Operates strictly on an in-memory SQLite database (`sqlite:///:memory:`).
- Explicitly enforces foreign keys via `PRAGMA foreign_keys=ON`.
- Never connects to or modifies MySQL.
- Does not depend on pandas or compiled ML extensions.
"""

from datetime import datetime, timezone
from typing import Dict, List, Set
import pytest
from sqlalchemy import create_engine, event, select, text
from sqlalchemy.orm import Session, sessionmaker

from app.models import (
    Base,
    MCAAcademicSession,
    MCAAssessmentEvent,
    MCAAttendanceSnapshot,
    MCACourse,
    MCACourseRegistration,
    MCACurriculumScheme,
    MCAFormativeSnapshot,
    MCAPredictionRecord,
    MCAProgram,
    MCAProjectMilestoneSnapshot,
    MCASemesterResult,
    MCASessionCourse,
    MCAStudent,
    PredictionRecord,
    Student,
)
from app.seeders.mca_curriculum_seeder import (
    CANONICAL_COURSES,
    CANONICAL_PROGRAM,
    CANONICAL_SCHEMES,
    CurriculumSeedMismatchError,
    CurriculumSeederError,
    seed_mca_curriculum,
)


# ===========================================================================
# Isolated SQLite Test Fixtures
# ===========================================================================

@pytest.fixture
def seeder_engine():
    """
    Provide an isolated in-memory SQLite database engine with foreign-key
    enforcement enabled via PRAGMA.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    yield engine
    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys=OFF"))
        Base.metadata.drop_all(bind=conn)
    engine.dispose()


@pytest.fixture
def seeder_session(seeder_engine) -> Session:
    """Provide a transactional session bound to the isolated in-memory engine."""
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=seeder_engine)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


# ===========================================================================
# 1. Structural Completeness & Semester Distribution
# ===========================================================================

def test_first_run_inserts_program_schemes_and_all_26_courses(seeder_session):
    """
    Requirement 1: Verify first execution inserts exactly 1 program, 2 schemes,
    and all 26 canonical courses.
    """
    result = seed_mca_curriculum(seeder_session, commit=True)

    assert result["status"] == "SUCCESS"
    assert result["program"]["action"] == "INSERTED"
    assert result["program"]["code"] == "MCA"
    assert result["schemes"]["inserted"] == 2
    assert result["schemes"]["unchanged"] == 0
    assert result["courses"]["inserted"] == 26
    assert result["courses"]["unchanged"] == 0
    assert result["courses"]["total"] == 26

    # Verify directly in database
    prog_count = seeder_session.query(MCAProgram).count()
    scheme_count = seeder_session.query(MCACurriculumScheme).count()
    course_count = seeder_session.query(MCACourse).count()

    assert prog_count == 1
    assert scheme_count == 2
    assert course_count == 26


def test_exact_semester_distribution(seeder_session):
    """
    Requirement 2: Verify exact course count per semester is 7 / 7 / 7 / 5.
    """
    seed_mca_curriculum(seeder_session, commit=True)

    sem1_courses = seeder_session.query(MCACourse).filter(MCACourse.semester_number == 1).all()
    sem2_courses = seeder_session.query(MCACourse).filter(MCACourse.semester_number == 2).all()
    sem3_courses = seeder_session.query(MCACourse).filter(MCACourse.semester_number == 3).all()
    sem4_courses = seeder_session.query(MCACourse).filter(MCACourse.semester_number == 4).all()

    assert len(sem1_courses) == 7, f"Expected 7 courses in Sem 1, found {len(sem1_courses)}"
    assert len(sem2_courses) == 7, f"Expected 7 courses in Sem 2, found {len(sem2_courses)}"
    assert len(sem3_courses) == 7, f"Expected 7 courses in Sem 3, found {len(sem3_courses)}"
    assert len(sem4_courses) == 5, f"Expected 5 courses in Sem 4, found {len(sem4_courses)}"
    assert len(sem1_courses) + len(sem2_courses) + len(sem3_courses) + len(sem4_courses) == 26


# ===========================================================================
# 2. Authoritative Course Titles & Types Reconciliation
# ===========================================================================

def test_every_course_title_matches_authoritative_list(seeder_session):
    """
    Requirement 3: Verify all 26 course titles in the database match the
    authoritative list exactly for each semester.
    """
    seed_mca_curriculum(seeder_session, commit=True)

    courses = seeder_session.query(MCACourse).all()
    courses_by_sem: Dict[int, List[str]] = {1: [], 2: [], 3: [], 4: []}
    for c in courses:
        courses_by_sem[c.semester_number].append(c.course_name)

    expected_sem1_titles = [
        "Operating System",
        "Programming and Problem Solving in C",
        "Mathematical Foundation",
        "Fundamentals of Computer Technologies",
        "Technical Communication",
        "Programming and Problem Solving in C Lab",
        "Operating System Lab",
    ]
    expected_sem2_titles = [
        "Database Management System",
        "Computer Network",
        "Object Oriented Programming with Java",
        "Software Engineering and UML",
        "Algorithm Design",
        "Java and OOPS Lab",
        "DBMS Lab",
    ]
    expected_sem3_titles = [
        "Data Mining",
        "Artificial Intelligence",
        "Elective-I: Python Programming",
        "Elective-II: Machine Learning and Deep Learning",
        "Elective-III: Distributed Systems",
        "Minor Project",
        "Elective-I Lab",
    ]
    expected_sem4_titles = [
        "Cloud Computing Technologies",
        "Cryptocurrency and Blockchain Technologies",
        "Advanced Python",
        "Information Security",
        "Big Data Analytics",
    ]

    assert set(courses_by_sem[1]) == set(expected_sem1_titles)
    assert set(courses_by_sem[2]) == set(expected_sem2_titles)
    assert set(courses_by_sem[3]) == set(expected_sem3_titles)
    assert set(courses_by_sem[4]) == set(expected_sem4_titles)


def test_every_course_semester_and_type_conformance(seeder_session):
    """
    Requirement 4: Verify every course has the correct semester (1-4) and course type.
    Use ONLY the four approved course types: 'theory', 'lab', 'elective', 'project'.
    Assert no unsupported types (e.g. 'CORE_ELECTIVE', 'SEMINAR') exist.
    """
    seed_mca_curriculum(seeder_session, commit=True)

    courses = seeder_session.query(MCACourse).all()
    assert len(courses) == 26

    allowed_types: Set[str] = {"theory", "lab", "elective", "project"}
    type_counts: Dict[str, int] = {}

    for c in courses:
        assert c.semester_number in (1, 2, 3, 4)
        assert c.course_type in allowed_types, f"Unsupported course_type: {c.course_type}"
        type_counts[c.course_type] = type_counts.get(c.course_type, 0) + 1

    # Verify expected course type counts across all 26 courses
    # Sem 1: 5 theory, 2 lab
    # Sem 2: 5 theory, 2 lab
    # Sem 3: 2 theory, 3 elective, 1 project, 1 lab
    # Sem 4: 5 theory
    # Totals: theory=17, lab=5, elective=3, project=1 (17 + 5 + 3 + 1 = 26)
    assert type_counts.get("theory") == 17
    assert type_counts.get("lab") == 5
    assert type_counts.get("elective") == 3
    assert type_counts.get("project") == 1
    assert "CORE_ELECTIVE" not in type_counts
    assert "SEMINAR" not in type_counts


def test_verified_codes_and_credits_semesters_1_and_3(seeder_session):
    """
    Requirement 5: Verify all 14 verified codes and credits match the approved catalogue.
    """
    seed_mca_curriculum(seeder_session, commit=True)

    expected_verified_courses = {
        # Semester 1 (7 courses)
        "MCA108": {"name": "Operating System", "type": "theory", "credits": 4, "sem": 1},
        "MCA109": {"name": "Programming and Problem Solving in C", "type": "theory", "credits": 4, "sem": 1},
        "MCA110": {"name": "Mathematical Foundation", "type": "theory", "credits": 4, "sem": 1},
        "MCA111": {"name": "Fundamentals of Computer Technologies", "type": "theory", "credits": 4, "sem": 1},
        "MCA112": {"name": "Technical Communication", "type": "theory", "credits": 4, "sem": 1},
        "MCA113": {"name": "Programming and Problem Solving in C Lab", "type": "lab", "credits": 8, "sem": 1},
        "MCA114": {"name": "Operating System Lab", "type": "lab", "credits": 4, "sem": 1},
        # Semester 3 (7 courses)
        "MCA301": {"name": "Data Mining", "type": "theory", "credits": 4, "sem": 3},
        "MCA302": {"name": "Artificial Intelligence", "type": "theory", "credits": 4, "sem": 3},
        "MCA303": {"name": "Elective-I: Python Programming", "type": "elective", "credits": 4, "sem": 3},
        "MCA304": {"name": "Elective-II: Machine Learning and Deep Learning", "type": "elective", "credits": 4, "sem": 3},
        "MCA305": {"name": "Elective-III: Distributed Systems", "type": "elective", "credits": 4, "sem": 3},
        "MCA306": {"name": "Minor Project", "type": "project", "credits": 8, "sem": 3},
        "MCA307": {"name": "Elective-I Lab", "type": "lab", "credits": 4, "sem": 3},
    }

    assert len(expected_verified_courses) == 14

    for code, spec in expected_verified_courses.items():
        course = seeder_session.query(MCACourse).filter_by(course_code=code).one_or_none()
        assert course is not None, f"Missing verified course: {code}"
        assert course.course_name == spec["name"], f"Name mismatch for {code}"
        assert course.course_type == spec["type"], f"Type mismatch for {code}"
        assert course.credits == spec["credits"], f"Credits mismatch for {code}"
        assert course.semester_number == spec["sem"], f"Semester mismatch for {code}"


# ===========================================================================
# 3. Scheme Association & Provisional Courses
# ===========================================================================

def test_provisional_courses_semesters_2_and_4(seeder_session):
    """
    Requirement 6: Verify Semesters 2 and 4 remain provisional:
    scheme_id is NULL, course_code is NULL, and credits is NULL.
    """
    seed_mca_curriculum(seeder_session, commit=True)

    # Semester 2 (7 courses)
    sem2_courses = seeder_session.query(MCACourse).filter_by(semester_number=2).all()
    assert len(sem2_courses) == 7
    for c in sem2_courses:
        assert c.scheme_id is None, f"Sem 2 course {c.course_name} must have scheme_id=NULL"
        assert c.course_code is None, f"Sem 2 course {c.course_name} must have course_code=NULL"
        assert c.credits is None, f"Sem 2 course {c.course_name} must have credits=NULL"

    # Semester 4 (5 courses)
    sem4_courses = seeder_session.query(MCACourse).filter_by(semester_number=4).all()
    assert len(sem4_courses) == 5
    for c in sem4_courses:
        assert c.scheme_id is None, f"Sem 4 course {c.course_name} must have scheme_id=NULL"
        assert c.course_code is None, f"Sem 4 course {c.course_name} must have course_code=NULL"
        assert c.credits is None, f"Sem 4 course {c.course_name} must have credits=NULL"


def test_official_scheme_associations_semesters_1_and_3(seeder_session):
    """
    Requirement 7: Verify only Semesters 1 and 3 are associated with their
    respective verified schemes (MCA-AUTONOMOUS-2025 and MCA-AUTONOMOUS-2024).
    """
    seed_mca_curriculum(seeder_session, commit=True)

    scheme_2025 = seeder_session.query(MCACurriculumScheme).filter_by(scheme_code="MCA-AUTONOMOUS-2025").one()
    scheme_2024 = seeder_session.query(MCACurriculumScheme).filter_by(scheme_code="MCA-AUTONOMOUS-2024").one()

    assert scheme_2025.effective_from == "July 2025"
    assert scheme_2024.effective_from == "July 2024"

    # Verify all 7 courses of Semester 1 reference scheme_2025
    sem1_courses = seeder_session.query(MCACourse).filter_by(semester_number=1).all()
    assert len(sem1_courses) == 7
    for c in sem1_courses:
        assert c.scheme_id == scheme_2025.id
        assert c.course_code is not None
        assert c.credits is not None

    # Verify all 7 courses of Semester 3 reference scheme_2024
    sem3_courses = seeder_session.query(MCACourse).filter_by(semester_number=3).all()
    assert len(sem3_courses) == 7
    for c in sem3_courses:
        assert c.scheme_id == scheme_2024.id
        assert c.course_code is not None
        assert c.credits is not None


# ===========================================================================
# 4. Idempotency & Repeat Execution Tests
# ===========================================================================

def test_second_run_creates_no_duplicates(seeder_session):
    """
    Requirement 8: Verify running seeder a second time creates no duplicates
    and reports zero inserted records.
    """
    res1 = seed_mca_curriculum(seeder_session, commit=True)
    assert res1["courses"]["inserted"] == 26

    res2 = seed_mca_curriculum(seeder_session, commit=True)

    assert res2["status"] == "SUCCESS"
    assert res2["program"]["action"] == "UNCHANGED"
    assert res2["schemes"]["inserted"] == 0
    assert res2["schemes"]["unchanged"] == 2
    assert res2["courses"]["inserted"] == 0
    assert res2["courses"]["unchanged"] == 26
    assert res2["courses"]["total"] == 26

    # Verify database counts are strictly unchanged
    assert seeder_session.query(MCAProgram).count() == 1
    assert seeder_session.query(MCACurriculumScheme).count() == 2
    assert seeder_session.query(MCACourse).count() == 26


def test_existing_matching_records_remain_unchanged(seeder_session):
    """
    Requirement 9: Verify pre-existing matching canonical records are preserved
    with identical primary keys.
    """
    pre_program = MCAProgram(
        program_name="Master of Computer Applications",
        program_code="MCA",
        duration_semesters=4,
    )
    seeder_session.add(pre_program)
    seeder_session.commit()
    pre_prog_id = pre_program.id

    result = seed_mca_curriculum(seeder_session, commit=True)

    assert result["program"]["action"] == "UNCHANGED"
    assert result["program"]["id"] == pre_prog_id

    post_program = seeder_session.query(MCAProgram).filter_by(program_code="MCA").one()
    assert post_program.id == pre_prog_id


# ===========================================================================
# 5. Mismatch Detection & Non-Destructive Rollback Tests
# ===========================================================================

def test_conflicting_program_causes_failure_and_rollback(seeder_session):
    """
    Requirement 10a: Verify pre-existing conflicting program causes CurriculumSeedMismatchError
    and rolls back without modifying existing records or seeding schemes/courses.
    """
    conflicting_prog = MCAProgram(
        program_name="Conflicting Engineering Program",  # Mismatch
        program_code="MCA",
        duration_semesters=4,
    )
    seeder_session.add(conflicting_prog)
    seeder_session.commit()

    with pytest.raises(CurriculumSeedMismatchError) as exc_info:
        seed_mca_curriculum(seeder_session, commit=True)

    assert "mca_programs" in str(exc_info.value)
    assert "program_name" in str(exc_info.value)

    # Verify transaction rolled back: no schemes or courses were inserted
    assert seeder_session.query(MCACurriculumScheme).count() == 0
    assert seeder_session.query(MCACourse).count() == 0

    # Verify conflicting row was NOT silently modified
    persisted_prog = seeder_session.query(MCAProgram).filter_by(program_code="MCA").one()
    assert persisted_prog.program_name == "Conflicting Engineering Program"


def test_conflicting_scheme_causes_failure_and_rollback(seeder_session):
    """
    Requirement 10b: Verify pre-existing conflicting scheme causes CurriculumSeedMismatchError
    and rolls back without inserting any courses.
    """
    program = MCAProgram(
        program_name="Master of Computer Applications",
        program_code="MCA",
        duration_semesters=4,
    )
    seeder_session.add(program)
    seeder_session.flush()

    conflicting_scheme = MCACurriculumScheme(
        program_id=program.id,
        scheme_name="Old Outdated Curriculum 2020",  # Mismatch
        scheme_code="MCA-AUTONOMOUS-2025",
        effective_from="July 2025",
        is_active=True,
    )
    seeder_session.add(conflicting_scheme)
    seeder_session.commit()

    with pytest.raises(CurriculumSeedMismatchError) as exc_info:
        seed_mca_curriculum(seeder_session, commit=True)

    assert "mca_curriculum_schemes" in str(exc_info.value)
    assert "scheme_name" in str(exc_info.value)

    # Verify transaction rolled back: no courses were inserted
    assert seeder_session.query(MCACourse).count() == 0


def test_conflicting_course_causes_failure_and_rollback(seeder_session):
    """
    Requirement 10c: Verify conflicting course attributes (e.g. credits mismatch) cause
    CurriculumSeedMismatchError and roll back completely.
    """
    seed_mca_curriculum(seeder_session, commit=True)

    course_os = seeder_session.query(MCACourse).filter_by(course_code="MCA108").one()
    course_os.credits = 2  # Authorized canonical is 4
    seeder_session.commit()

    with pytest.raises(CurriculumSeedMismatchError) as exc_info:
        seed_mca_curriculum(seeder_session, commit=True)

    assert "mca_courses" in str(exc_info.value)
    assert "credits" in str(exc_info.value)


# ===========================================================================
# 6. Isolation & Zero Downstream Records Tests
# ===========================================================================

def test_no_academic_sessions_created(seeder_session):
    """
    Requirement 11a: Verify the curriculum seeder creates zero academic session records.
    """
    seed_mca_curriculum(seeder_session, commit=True)
    count = seeder_session.query(MCAAcademicSession).count()
    assert count == 0, f"Expected 0 academic sessions, found {count}"


def test_no_session_courses_created(seeder_session):
    """
    Requirement 11b: Verify the curriculum seeder creates zero session-course mappings.
    """
    seed_mca_curriculum(seeder_session, commit=True)
    count = seeder_session.query(MCASessionCourse).count()
    assert count == 0, f"Expected 0 session-course mappings, found {count}"


def test_no_downstream_records_created(seeder_session):
    """
    Requirement 11c: Verify no students, registrations, assessment events, snapshots,
    results, or prediction records are created by the curriculum seeder.
    """
    seed_mca_curriculum(seeder_session, commit=True)

    assert seeder_session.query(MCAStudent).count() == 0
    assert seeder_session.query(MCACourseRegistration).count() == 0
    assert seeder_session.query(MCAAssessmentEvent).count() == 0
    assert seeder_session.query(MCAAttendanceSnapshot).count() == 0
    assert seeder_session.query(MCAFormativeSnapshot).count() == 0
    assert seeder_session.query(MCAProjectMilestoneSnapshot).count() == 0
    assert seeder_session.query(MCASemesterResult).count() == 0
    assert seeder_session.query(MCAPredictionRecord).count() == 0


# ===========================================================================
# 7. Phase 1 UCI Infrastructure Unaffected
# ===========================================================================

def test_phase1_uci_infrastructure_unaffected(seeder_session):
    """
    Requirement 12: Verify existing Phase 1 UCI models and records are completely
    preserved and unaffected by the MCA curriculum seeder.
    """
    # Pre-insert Phase 1 UCI student and prediction record
    uci_student = Student(
        student_code="UCI-TEST-001",
    )
    seeder_session.add(uci_student)
    seeder_session.commit()

    uci_pred = PredictionRecord(
        student_id=uci_student.id,
        subject="Mathematics",
        scenario="Scenario A",
        model_name="logistic_regression",
        model_version="1.0.0",
        predicted_category="Good",
        input_features={"studytime": 3, "failures": 0},
        recommendations={"strengths": ["Consistent study habits"]},
    )
    seeder_session.add(uci_pred)
    seeder_session.commit()

    # Run MCA curriculum seeder
    result = seed_mca_curriculum(seeder_session, commit=True)
    assert result["status"] == "SUCCESS"

    # Verify Phase 1 records remain unchanged
    refreshed_student = seeder_session.get(Student, uci_student.id)
    assert refreshed_student is not None
    assert refreshed_student.student_code == "UCI-TEST-001"

    refreshed_pred = seeder_session.get(PredictionRecord, uci_pred.id)
    assert refreshed_pred is not None
    assert refreshed_pred.predicted_category == "Good"
    assert refreshed_pred.student_id == uci_student.id
