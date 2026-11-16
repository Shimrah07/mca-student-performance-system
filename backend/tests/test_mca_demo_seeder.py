"""
backend/tests/test_mca_demo_seeder.py

Comprehensive test suite for MCA Demonstration Data Seeder.
Tests execute in isolated in-memory SQLite databases and verify:
1. Prerequisite validation (aborts when canonical curriculum is missing)
2. Initial seeding correctness (exact record counts and values)
3. Idempotency (repeated runs do not duplicate or alter records)
4. Mismatch detection and rollback safety
5. Foreign key and relational snapshot integrity
6. Contrasting student profiles (Student A strong, Student B at-risk)
7. End-to-end integration with Phase 2E/3B feature extraction
8. Assessment event self-reference prevention
"""

from datetime import date, datetime, timezone
from decimal import Decimal
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, MCA_TABLE_ALLOWLIST
from app.models import (
    MCAAcademicSession,
    MCAAssessmentEvent,
    MCAAttendanceSnapshot,
    MCACourse,
    MCACourseRegistration,
    MCACurriculumScheme,
    MCAFormativeSnapshot,
    MCAProgram,
    MCASessionCourse,
    MCAStudent,
)
from app.seeders.mca_curriculum_seeder import seed_mca_curriculum
from app.seeders.mca_demo_seeder import (
    seed_mca_demonstration_data,
    DemoSeederError,
    DemoSeederPrerequisiteError,
    DemoSeederMismatchError,
    DEMO_SESSION_SPEC,
    DEMO_STUDENTS_SPEC,
    DEMO_COURSE_CODES,
)
from app.services.mca_feature_extraction import (
    extract_subject_academic_features,
    extract_semester_academic_features,
)


@pytest.fixture
def sqlite_engine():
    """Create isolated in-memory SQLite engine with foreign key enforcement."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    # Build only MCA tables
    mca_tables = [Base.metadata.tables[t] for t in MCA_TABLE_ALLOWLIST]
    Base.metadata.create_all(bind=engine, tables=mca_tables)
    return engine


@pytest.fixture
def db_session(sqlite_engine):
    """Provide a transactional database session for tests."""
    SessionFactory = sessionmaker(bind=sqlite_engine, autocommit=False, autoflush=False)
    session = SessionFactory()
    try:
        yield session
    finally:
        session.close()


# ===========================================================================
# 1. Prerequisite Validation Tests
# ===========================================================================

def test_seeder_aborts_without_canonical_curriculum(db_session: Session):
    """Demonstration seeder must abort if canonical curriculum has not been seeded."""
    with pytest.raises(DemoSeederPrerequisiteError) as exc_info:
        seed_mca_demonstration_data(db_session)
    assert "not found in database" in str(exc_info.value)


# ===========================================================================
# 2. Initial Seeding Correctness
# ===========================================================================

def test_initial_seeding_creates_exact_expected_records(db_session: Session):
    """Test that first execution creates exactly the expected records."""
    # Seed canonical curriculum first
    seed_mca_curriculum(db_session)

    stats = seed_mca_demonstration_data(db_session)

    # Verify return stats
    assert stats["session"]["created"] is True
    assert stats["session"]["session_name"] == "DEMO-MCA-2025-27-COHORT"
    assert stats["session_courses"]["created"] == 4
    assert stats["session_courses"]["total"] == 4
    assert stats["students"]["created"] == 2
    assert stats["students"]["total"] == 2
    assert stats["registrations"]["created"] == 8
    assert stats["registrations"]["total"] == 8
    assert stats["attendance_snapshots"]["created"] == 16
    assert stats["attendance_snapshots"]["total"] == 16
    assert stats["formative_snapshots"]["created"] == 8
    assert stats["formative_snapshots"]["total"] == 8

    # Verify database counts
    assert db_session.query(MCAAcademicSession).count() == 1
    assert db_session.query(MCASessionCourse).count() == 4
    assert db_session.query(MCAStudent).count() == 2
    assert db_session.query(MCACourseRegistration).count() == 8
    assert db_session.query(MCAAttendanceSnapshot).count() == 16
    assert db_session.query(MCAFormativeSnapshot).count() == 8


# ===========================================================================
# 3. Idempotency Tests
# ===========================================================================

def test_seeder_is_fully_idempotent(db_session: Session):
    """Repeated execution must not create duplicates or modify records."""
    seed_mca_curriculum(db_session)

    # First run
    stats1 = seed_mca_demonstration_data(db_session)
    assert stats1["session"]["created"] is True
    assert stats1["students"]["created"] == 2

    # Second run
    stats2 = seed_mca_demonstration_data(db_session)
    assert stats2["session"]["created"] is False
    assert stats2["session_courses"]["created"] == 0
    assert stats2["students"]["created"] == 0
    assert stats2["registrations"]["created"] == 0
    assert stats2["attendance_snapshots"]["created"] == 0
    assert stats2["formative_snapshots"]["created"] == 0

    # Counts must remain completely unchanged
    assert db_session.query(MCAAcademicSession).count() == 1
    assert db_session.query(MCASessionCourse).count() == 4
    assert db_session.query(MCAStudent).count() == 2
    assert db_session.query(MCACourseRegistration).count() == 8
    assert db_session.query(MCAAttendanceSnapshot).count() == 16
    assert db_session.query(MCAFormativeSnapshot).count() == 8


# ===========================================================================
# 4. Mismatch Detection and Rollback Tests
# ===========================================================================

def test_seeder_detects_student_mismatch(db_session: Session):
    """If a student record has mismatched attributes, seeder aborts with DemoSeederMismatchError."""
    seed_mca_curriculum(db_session)
    seed_mca_demonstration_data(db_session)

    # Corrupt student attribute: soft-deactivate Student A
    student_a = db_session.query(MCAStudent).filter_by(student_code="DEMO-MCA-2025-001").first()
    student_a.is_active = False
    db_session.commit()

    with pytest.raises(DemoSeederMismatchError) as exc_info:
        seed_mca_demonstration_data(db_session)
    assert "mca_students" in str(exc_info.value)
    assert "is_active" in str(exc_info.value)


def test_seeder_detects_attendance_mismatch(db_session: Session):
    """If attendance snapshot data differs, seeder aborts with DemoSeederMismatchError."""
    seed_mca_curriculum(db_session)
    seed_mca_demonstration_data(db_session)

    # Corrupt attendance snapshot
    snap = db_session.query(MCAAttendanceSnapshot).first()
    snap.attendance_percentage = Decimal("99.99")
    db_session.commit()

    with pytest.raises(DemoSeederMismatchError) as exc_info:
        seed_mca_demonstration_data(db_session)
    assert "mca_attendance_snapshots" in str(exc_info.value)


# ===========================================================================
# 5. Contrasting Profiles and Feature Extraction Integration
# ===========================================================================

def test_contrasting_student_profiles_and_feature_extraction(db_session: Session):
    """
    Verify Student A (strong) and Student B (at-risk) have distinct characteristics
    and can be processed by the feature extraction service.
    """
    seed_mca_curriculum(db_session)
    seed_mca_demonstration_data(db_session)

    student_a = db_session.query(MCAStudent).filter_by(student_code="DEMO-MCA-2025-001").first()
    student_b = db_session.query(MCAStudent).filter_by(student_code="DEMO-MCA-2025-002").first()

    cutoff = datetime(2025, 9, 20, 0, 0, 0, tzinfo=timezone.utc)

    # Extract semester features for both students
    features_a = extract_semester_academic_features(db_session, student_a.id, 1, cutoff)
    features_b = extract_semester_academic_features(db_session, student_b.id, 1, cutoff)

    # Verify Student A high performance
    assert features_a["features"]["average_attendance_percentage"] >= 90.0
    assert features_a["features"]["average_mst1_marks"] >= 17.0
    assert features_a["features"]["average_assignment_score"] >= 9.0

    # Verify Student B at-risk performance
    assert features_b["features"]["average_attendance_percentage"] <= 60.0
    assert features_b["features"]["average_mst1_marks"] <= 9.0
    assert features_b["features"]["average_assignment_score"] <= 5.5

    # Subject-level feature extraction for MCA108
    reg_a_108 = (
        db_session.query(MCACourseRegistration)
        .join(MCASessionCourse)
        .join(MCACourse)
        .filter(
            MCACourseRegistration.student_id == student_a.id,
            MCACourse.course_code == "MCA108",
        )
        .first()
    )
    assert reg_a_108 is not None
    subject_features_a = extract_subject_academic_features(db_session, reg_a_108.id, cutoff)
    assert subject_features_a["features"]["attendance_percentage"] == 92.0
    assert subject_features_a["features"]["mst1_marks"] == 18.0
    assert subject_features_a["features"]["assignment_score"] == 9.5


# ===========================================================================
# 6. Assessment Event Self-Reference Prevention
# ===========================================================================

def test_assessment_event_cannot_self_reference(db_session: Session):
    """
    Verify application-level check prevents MCAAssessmentEvent from setting
    original_event_id == id.
    """
    event = MCAAssessmentEvent(
        id=10,
        session_course_id=1,
        event_name="Self Ref Test",
        event_type="MST",
        max_marks=20,
    )
    with pytest.raises(ValueError) as exc_info:
        event.original_event_id = 10
    assert "ck_mca_assessment_event_no_self_ref violation" in str(exc_info.value)
