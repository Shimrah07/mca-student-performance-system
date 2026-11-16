"""
backend/tests/test_mca_feature_extraction_and_persistence.py

Automated test suite for Phase 2E: Academic Feature Extraction & Prediction Persistence.
Verifies all 20 required validation scenarios in an isolated in-memory SQLite database
with PRAGMA foreign_keys=ON:

1. Correct extraction of eligible attendance snapshots.
2. Correct extraction of formative snapshots.
3. Correct extraction of project milestone snapshots.
4. Latest eligible revision selection.
5. Exclusion of revisions after cutoff.
6. Inclusion of eligible previous semester results.
7. Exclusion of results with NULL declared_at.
8. Exclusion of results declared after cutoff.
9. Exclusion of results recorded after cutoff.
10. Exclusion of current and future semester results.
11. No target-result data leakage.
12. Subject-level and semester-level scope separation.
13. Explicit handling of missing academic data.
14. Deterministic feature extraction for identical inputs.
15. Successful prediction persistence.
16. Multiple predictions remain independently stored.
17. Exact cutoff timestamp preservation.
18. Transaction rollback on persistence failure.
19. Existing foreign-key and nullability rules are respected.
20. Phase 1 UCI models and functionality remain unaffected.

Strict isolation:
- Operates strictly on an in-memory SQLite database (sqlite:///:memory:).
- Explicitly enforces foreign keys via PRAGMA foreign_keys=ON.
- Never connects to or modifies MySQL.
- Does not depend on pandas or compiled ML extensions.
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict
import pytest
from sqlalchemy import create_engine, event, select, text
from sqlalchemy.orm import Session, sessionmaker

from app.models import (
    Base,
    MCAAcademicSession,
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
from app.services.mca_feature_extraction import (
    EntityNotFoundError,
    FeatureExtractionError,
    InvalidCutoffTimestampError,
    InvalidPredictionScopeError,
    extract_academic_features,
    extract_semester_academic_features,
    extract_subject_academic_features,
)
from app.services.mca_prediction_service import (
    InvalidPredictionPayloadError,
    PredictionPersistenceError,
    get_mca_prediction_by_id,
    list_mca_predictions_by_registration,
    list_mca_predictions_by_student,
    persist_mca_prediction,
)


# ===========================================================================
# Isolated SQLite Test Fixtures
# ===========================================================================

@pytest.fixture
def mca_engine():
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
def session(mca_engine) -> Session:
    """Provide a transactional session bound to the isolated in-memory engine."""
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=mca_engine)
    sess = TestSessionLocal()
    try:
        yield sess
    finally:
        sess.close()


@pytest.fixture
def mca_environment(session: Session) -> Dict[str, Any]:
    """
    Populate a complete, realistic academic hierarchy for testing:
    - MCA Program
    - Scheme: MCA-AUTONOMOUS-2025
    - Academic Session: MCA 2025-27 Batch
    - Courses:
        * Sem 1: MCA108 (Operating System, theory, 4 credits)
        * Sem 1: MCA113 (Programming in C Lab, lab, 8 credits)
        * Sem 3: MCA306 (Minor Project, project, 8 credits)
    - Session Courses
    - Enrolled Student: MCA-2025-001
    - Active Registrations
    """
    # 1. Program
    program = MCAProgram(
        program_name="Master of Computer Applications",
        program_code="MCA",
        duration_semesters=4,
    )
    session.add(program)
    session.flush()

    # 2. Scheme
    scheme = MCACurriculumScheme(
        program_id=program.id,
        scheme_name="UIT-RGPV Autonomous MCA Scheme (July 2025)",
        scheme_code="MCA-AUTONOMOUS-2025",
        effective_from="July 2025",
        is_active=True,
    )
    session.add(scheme)
    session.flush()

    # 3. Academic Session
    acad_session = MCAAcademicSession(
        scheme_id=scheme.id,
        session_name="MCA 2025-27 Batch",
        batch_year="2025-2027",
        start_date=date(2025, 7, 1),
        end_date=date(2027, 6, 30),
        is_active=True,
    )
    session.add(acad_session)
    session.flush()

    # 4. Courses
    course_os = MCACourse(
        program_id=program.id,
        scheme_id=scheme.id,
        course_code="MCA108",
        course_name="Operating System",
        semester_number=1,
        course_type="theory",
        credits=4,
    )
    course_lab = MCACourse(
        program_id=program.id,
        scheme_id=scheme.id,
        course_code="MCA113",
        course_name="Programming and Problem Solving in C Lab",
        semester_number=1,
        course_type="lab",
        credits=8,
    )
    course_proj = MCACourse(
        program_id=program.id,
        scheme_id=scheme.id,
        course_code="MCA306",
        course_name="Minor Project",
        semester_number=3,
        course_type="project",
        credits=8,
    )
    session.add_all([course_os, course_lab, course_proj])
    session.flush()

    # 5. Session Courses
    sc_os = MCASessionCourse(session_id=acad_session.id, course_id=course_os.id)
    sc_lab = MCASessionCourse(session_id=acad_session.id, course_id=course_lab.id)
    sc_proj = MCASessionCourse(session_id=acad_session.id, course_id=course_proj.id)
    session.add_all([sc_os, sc_lab, sc_proj])
    session.flush()

    # 6. Student
    student = MCAStudent(
        student_code="MCA-2025-001",
        session_id=acad_session.id,
        is_active=True,
    )
    session.add(student)
    session.flush()

    # 7. Registrations
    reg_os = MCACourseRegistration(
        student_id=student.id,
        session_course_id=sc_os.id,
        semester_number=1,
        attempt_type="regular",
        is_active=True,
    )
    reg_lab = MCACourseRegistration(
        student_id=student.id,
        session_course_id=sc_lab.id,
        semester_number=1,
        attempt_type="regular",
        is_active=True,
    )
    reg_proj = MCACourseRegistration(
        student_id=student.id,
        session_course_id=sc_proj.id,
        semester_number=3,
        attempt_type="regular",
        is_active=True,
    )
    session.add_all([reg_os, reg_lab, reg_proj])
    session.commit()

    return {
        "program": program,
        "scheme": scheme,
        "session": acad_session,
        "course_os": course_os,
        "course_lab": course_lab,
        "course_proj": course_proj,
        "sc_os": sc_os,
        "sc_lab": sc_lab,
        "sc_proj": sc_proj,
        "student": student,
        "reg_os": reg_os,
        "reg_lab": reg_lab,
        "reg_proj": reg_proj,
    }


# ===========================================================================
# 1. Feature Extraction: Attendance Snapshots
# ===========================================================================

def test_extract_eligible_attendance_snapshots(session, mca_environment):
    """
    Test 1: Verify correct extraction of eligible attendance snapshot fields
    (attendance_percentage, classes_held, classes_attended).
    """
    env = mca_environment
    base_time = datetime(2025, 9, 15, 10, 0, 0)

    snap = MCAAttendanceSnapshot(
        registration_id=env["reg_os"].id,
        revision_number=1,
        recorded_at=base_time,
        attendance_percentage=Decimal("85.50"),
        classes_held=40,
        classes_attended=34,
    )
    session.add(snap)
    session.commit()

    cutoff = base_time + timedelta(hours=1)
    result = extract_subject_academic_features(session, env["reg_os"].id, cutoff)

    assert result["metadata"]["registration_id"] == env["reg_os"].id
    assert result["features"]["attendance_percentage"] == 85.50
    assert result["features"]["classes_held"] == 40
    assert result["features"]["classes_attended"] == 34
    assert result["metadata"]["included_snapshots"]["attendance"]["revision_number"] == 1


# ===========================================================================
# 2. Feature Extraction: Formative Snapshots
# ===========================================================================

def test_extract_eligible_formative_snapshots(session, mca_environment):
    """
    Test 2: Verify correct extraction of eligible formative snapshot fields
    (mst1_marks, mst2_marks, assignment_score, viva_marks, lab_record_score).
    """
    env = mca_environment
    base_time = datetime(2025, 10, 1, 12, 0, 0)

    snap = MCAFormativeSnapshot(
        registration_id=env["reg_os"].id,
        revision_number=1,
        recorded_at=base_time,
        mst1_marks=Decimal("17.50"),
        mst2_marks=Decimal("18.00"),
        assignment_score=Decimal("8.50"),
        viva_marks=Decimal("16.00"),
        lab_record_score=Decimal("9.00"),
    )
    session.add(snap)
    session.commit()

    cutoff = base_time + timedelta(hours=2)
    result = extract_subject_academic_features(session, env["reg_os"].id, cutoff)

    assert result["features"]["mst1_marks"] == 17.50
    assert result["features"]["mst2_marks"] == 18.00
    assert result["features"]["assignment_score"] == 8.50
    assert result["features"]["viva_marks"] == 16.00
    assert result["features"]["lab_record_score"] == 9.00
    assert result["metadata"]["included_snapshots"]["formative"]["revision_number"] == 1


# ===========================================================================
# 3. Feature Extraction: Project Milestone Snapshots
# ===========================================================================

def test_extract_eligible_project_milestone_snapshots(session, mca_environment):
    """
    Test 3: Verify correct extraction of project milestone snapshot fields
    (synopsis_approved, design_score, implementation_pct, supervisor_score).
    """
    env = mca_environment
    base_time = datetime(2026, 9, 20, 15, 0, 0)

    snap = MCAProjectMilestoneSnapshot(
        registration_id=env["reg_proj"].id,
        revision_number=1,
        recorded_at=base_time,
        synopsis_approved=True,
        design_score=Decimal("9.00"),
        implementation_pct=Decimal("65.00"),
        supervisor_score=Decimal("8.50"),
    )
    session.add(snap)
    session.commit()

    cutoff = base_time + timedelta(hours=1)
    result = extract_subject_academic_features(session, env["reg_proj"].id, cutoff)

    assert result["features"]["synopsis_approved"] is True
    assert result["features"]["design_score"] == 9.00
    assert result["features"]["implementation_pct"] == 65.00
    assert result["features"]["supervisor_score"] == 8.50
    assert result["metadata"]["included_snapshots"]["milestone"]["revision_number"] == 1


# ===========================================================================
# 4. Latest Eligible Revision Selection
# ===========================================================================

def test_latest_eligible_revision_selection(session, mca_environment):
    """
    Test 4: Verify latest eligible revision is selected when multiple revisions
    exist prior to cutoff.
    """
    env = mca_environment
    t1 = datetime(2025, 9, 10, 10, 0, 0)
    t2 = datetime(2025, 9, 20, 10, 0, 0)
    t3 = datetime(2025, 9, 30, 10, 0, 0)

    # Insert 3 revisions of attendance
    session.add(MCAAttendanceSnapshot(
        registration_id=env["reg_os"].id,
        revision_number=1,
        recorded_at=t1,
        attendance_percentage=Decimal("70.00"),
    ))
    session.add(MCAAttendanceSnapshot(
        registration_id=env["reg_os"].id,
        revision_number=2,
        recorded_at=t2,
        attendance_percentage=Decimal("80.00"),
    ))
    session.add(MCAAttendanceSnapshot(
        registration_id=env["reg_os"].id,
        revision_number=3,
        recorded_at=t3,
        attendance_percentage=Decimal("90.00"),
    ))
    session.commit()

    # Cutoff between revision 2 and revision 3 (e.g. 2025-09-25)
    cutoff = datetime(2025, 9, 25, 0, 0, 0)
    result = extract_subject_academic_features(session, env["reg_os"].id, cutoff)

    # Must pick revision 2 (recorded at t2 <= cutoff)
    assert result["metadata"]["included_snapshots"]["attendance"]["revision_number"] == 2
    assert result["features"]["attendance_percentage"] == 80.00


# ===========================================================================
# 5. Exclusion of Revisions After Cutoff
# ===========================================================================

def test_exclusion_of_revisions_after_cutoff(session, mca_environment):
    """
    Test 5: Verify revisions recorded strictly after cutoff timestamp are excluded.
    """
    env = mca_environment
    t1 = datetime(2025, 9, 10, 10, 0, 0)
    t2 = datetime(2025, 9, 20, 10, 0, 0)

    session.add(MCAAttendanceSnapshot(
        registration_id=env["reg_os"].id,
        revision_number=1,
        recorded_at=t1,
        attendance_percentage=Decimal("75.00"),
    ))
    session.add(MCAAttendanceSnapshot(
        registration_id=env["reg_os"].id,
        revision_number=2,
        recorded_at=t2,
        attendance_percentage=Decimal("95.00"),
    ))
    session.commit()

    # Cutoff prior to t2 (e.g. 2025-09-15)
    cutoff = datetime(2025, 9, 15, 0, 0, 0)
    result = extract_subject_academic_features(session, env["reg_os"].id, cutoff)

    # Revision 2 must NOT be present
    assert result["metadata"]["included_snapshots"]["attendance"]["revision_number"] == 1
    assert result["features"]["attendance_percentage"] == 75.00


# ===========================================================================
# 6. Inclusion of Eligible Previous Semester Results
# ===========================================================================

def test_inclusion_of_eligible_previous_semester_results(session, mca_environment):
    """
    Test 6: Verify prior semester results are included when declared and recorded
    before cutoff for a student predicting a subsequent semester.
    """
    env = mca_environment
    # Registration is for Semester 3 (Minor Project)
    reg_proj_id = env["reg_proj"].id

    t_dec1 = datetime(2026, 1, 15, 12, 0, 0)
    t_rec1 = datetime(2026, 1, 16, 10, 0, 0)
    t_dec2 = datetime(2026, 6, 20, 12, 0, 0)
    t_rec2 = datetime(2026, 6, 21, 10, 0, 0)

    # Semester 1 result
    session.add(MCASemesterResult(
        student_id=env["student"].id,
        session_id=env["session"].id,
        semester_number=1,
        sgpa=Decimal("8.20"),
        cgpa=Decimal("8.20"),
        declared_at=t_dec1,
        recorded_at=t_rec1,
    ))
    # Semester 2 result
    session.add(MCASemesterResult(
        student_id=env["student"].id,
        session_id=env["session"].id,
        semester_number=2,
        sgpa=Decimal("8.60"),
        cgpa=Decimal("8.40"),
        declared_at=t_dec2,
        recorded_at=t_rec2,
    ))
    session.commit()

    # Cutoff in Semester 3 (2026-08-01)
    cutoff = datetime(2026, 8, 1, 0, 0, 0)
    result = extract_subject_academic_features(session, reg_proj_id, cutoff)

    assert result["features"]["prior_semesters_completed"] == 2
    assert result["features"]["latest_prior_sgpa"] == 8.60
    assert result["features"]["cumulative_prior_sgpa_avg"] == 8.40
    assert result["features"]["latest_declared_cgpa"] == 8.40
    assert len(result["metadata"]["included_semester_results"]) == 2


# ===========================================================================
# 7. Exclusion of Results with NULL declared_at
# ===========================================================================

def test_exclusion_of_results_with_null_declared_at(session, mca_environment):
    """
    Test 7: Verify semester results with declared_at=NULL (provisional) are strictly
    excluded from automated prior performance metrics.
    """
    env = mca_environment
    reg_proj_id = env["reg_proj"].id  # Semester 3

    # Provisional Semester 1 result with NULL declared_at
    session.add(MCASemesterResult(
        student_id=env["student"].id,
        session_id=env["session"].id,
        semester_number=1,
        sgpa=Decimal("8.00"),
        cgpa=Decimal("8.00"),
        declared_at=None,  # Provisional!
        recorded_at=datetime(2026, 1, 10, 10, 0, 0),
    ))
    session.commit()

    cutoff = datetime(2026, 8, 1, 0, 0, 0)
    result = extract_subject_academic_features(session, reg_proj_id, cutoff)

    assert result["features"]["prior_semesters_completed"] == 0
    assert result["features"]["latest_prior_sgpa"] is None
    assert len(result["metadata"]["included_semester_results"]) == 0


# ===========================================================================
# 8. Exclusion of Results Declared After Cutoff
# ===========================================================================

def test_exclusion_of_results_declared_after_cutoff(session, mca_environment):
    """
    Test 8: Verify semester results declared after cutoff timestamp are excluded.
    """
    env = mca_environment
    reg_proj_id = env["reg_proj"].id

    t_dec = datetime(2026, 7, 10, 12, 0, 0)  # Declared July 10
    t_rec = datetime(2026, 6, 1, 10, 0, 0)   # Recorded June 1

    session.add(MCASemesterResult(
        student_id=env["student"].id,
        session_id=env["session"].id,
        semester_number=1,
        sgpa=Decimal("8.50"),
        cgpa=Decimal("8.50"),
        declared_at=t_dec,
        recorded_at=t_rec,
    ))
    session.commit()

    # Cutoff is July 1 (before declaration on July 10)
    cutoff = datetime(2026, 7, 1, 0, 0, 0)
    result = extract_subject_academic_features(session, reg_proj_id, cutoff)

    assert result["features"]["prior_semesters_completed"] == 0
    assert result["features"]["latest_prior_sgpa"] is None


# ===========================================================================
# 9. Exclusion of Results Recorded After Cutoff
# ===========================================================================

def test_exclusion_of_results_recorded_after_cutoff(session, mca_environment):
    """
    Test 9: Verify semester results recorded in DB after cutoff are excluded
    even if the declared_at timestamp is before cutoff.
    """
    env = mca_environment
    reg_proj_id = env["reg_proj"].id

    t_dec = datetime(2026, 1, 15, 12, 0, 0)  # Declared Jan 15
    t_rec = datetime(2026, 7, 20, 10, 0, 0)  # Recorded July 20

    session.add(MCASemesterResult(
        student_id=env["student"].id,
        session_id=env["session"].id,
        semester_number=1,
        sgpa=Decimal("8.50"),
        cgpa=Decimal("8.50"),
        declared_at=t_dec,
        recorded_at=t_rec,
    ))
    session.commit()

    # Cutoff is March 1 (after declaration, but before DB recording)
    cutoff = datetime(2026, 3, 1, 0, 0, 0)
    result = extract_subject_academic_features(session, reg_proj_id, cutoff)

    assert result["features"]["prior_semesters_completed"] == 0
    assert result["features"]["latest_prior_sgpa"] is None


# ===========================================================================
# 10. Exclusion of Current and Future Semester Results
# ===========================================================================

def test_exclusion_of_current_and_future_semester_results(session, mca_environment):
    """
    Test 10: Verify results for semester_number >= target_semester are strictly excluded.
    """
    env = mca_environment
    reg_os_id = env["reg_os"].id  # Target semester = 1

    t_dec = datetime(2025, 12, 1, 12, 0, 0)
    t_rec = datetime(2025, 12, 2, 10, 0, 0)

    # Insert Semester 1 result (same as target semester) and Semester 2 result
    session.add(MCASemesterResult(
        student_id=env["student"].id,
        session_id=env["session"].id,
        semester_number=1,
        sgpa=Decimal("9.00"),
        cgpa=Decimal("9.00"),
        declared_at=t_dec,
        recorded_at=t_rec,
    ))
    session.add(MCASemesterResult(
        student_id=env["student"].id,
        session_id=env["session"].id,
        semester_number=2,
        sgpa=Decimal("8.50"),
        cgpa=Decimal("8.75"),
        declared_at=t_dec,
        recorded_at=t_rec,
    ))
    session.commit()

    cutoff = datetime(2026, 1, 1, 0, 0, 0)
    result = extract_subject_academic_features(session, reg_os_id, cutoff)

    # Target is semester 1, so no prior semester exists (< 1)
    assert result["features"]["prior_semesters_completed"] == 0
    assert result["features"]["latest_prior_sgpa"] is None
    assert len(result["metadata"]["included_semester_results"]) == 0


# ===========================================================================
# 11. No Target-Result Data Leakage
# ===========================================================================

def test_no_target_result_data_leakage(session, mca_environment):
    """
    Test 11: Explicitly verify that even if the student already has a declared result
    for the target semester in the database, it is NEVER leaked into the input features.
    """
    env = mca_environment
    student_id = env["student"].id

    t_past = datetime(2025, 12, 15, 12, 0, 0)

    # Student has completed Semester 1 with declared result
    session.add(MCASemesterResult(
        student_id=student_id,
        session_id=env["session"].id,
        semester_number=1,
        sgpa=Decimal("8.80"),
        cgpa=Decimal("8.80"),
        declared_at=t_past,
        recorded_at=t_past,
    ))
    session.commit()

    # Predicting Semester 1 (e.g. backtesting)
    cutoff = datetime(2026, 1, 1, 0, 0, 0)
    res_sem1 = extract_semester_academic_features(session, student_id, target_semester=1, cutoff_timestamp=cutoff)

    # Must NOT include the Semester 1 final result!
    assert res_sem1["features"]["prior_semesters_completed"] == 0
    assert res_sem1["features"]["latest_prior_sgpa"] is None
    for r in res_sem1["metadata"]["included_semester_results"]:
        assert r["semester_number"] < 1, "Target semester result leaked into features!"


# ===========================================================================
# 12. Scope Separation: Subject-Level vs Semester-Level
# ===========================================================================

def test_subject_level_and_semester_level_scope_separation(session, mca_environment):
    """
    Test 12: Verify subject-level and semester-level prediction scopes are
    distinct in structure, metadata, and aggregated metrics.
    """
    env = mca_environment
    cutoff = datetime(2025, 10, 15, 0, 0, 0)

    # Add attendance for both Semester 1 courses
    session.add(MCAAttendanceSnapshot(
        registration_id=env["reg_os"].id,
        revision_number=1,
        recorded_at=datetime(2025, 10, 1, 10, 0, 0),
        attendance_percentage=Decimal("90.00"),
    ))
    session.add(MCAAttendanceSnapshot(
        registration_id=env["reg_lab"].id,
        revision_number=1,
        recorded_at=datetime(2025, 10, 1, 10, 0, 0),
        attendance_percentage=Decimal("80.00"),
    ))
    session.commit()

    # 1. Subject-level extraction
    subject_res = extract_subject_academic_features(session, env["reg_os"].id, cutoff)
    assert subject_res["metadata"]["prediction_scope"] == "subject"
    assert subject_res["metadata"]["registration_id"] == env["reg_os"].id
    assert subject_res["features"]["attendance_percentage"] == 90.00

    # 2. Semester-level extraction
    semester_res = extract_semester_academic_features(session, env["student"].id, target_semester=1, cutoff_timestamp=cutoff)
    assert semester_res["metadata"]["prediction_scope"] == "semester"
    assert "registration_ids" in semester_res["metadata"]
    assert env["reg_os"].id in semester_res["metadata"]["registration_ids"]
    assert env["reg_lab"].id in semester_res["metadata"]["registration_ids"]
    # Aggregated metrics: avg(90, 80) = 85.00, min(90, 80) = 80.00
    assert semester_res["features"]["average_attendance_percentage"] == 85.00
    assert semester_res["features"]["min_attendance_percentage"] == 80.00


# ===========================================================================
# 13. Explicit Handling of Missing Academic Data
# ===========================================================================

def test_explicit_handling_of_missing_academic_data(session, mca_environment):
    """
    Test 13: Verify missing academic data is represented explicitly as None
    and never converted into fabricated values (e.g. 0% or default 75%).
    """
    env = mca_environment
    cutoff = datetime(2025, 8, 1, 0, 0, 0)

    # No snapshots or previous results have been seeded
    result = extract_subject_academic_features(session, env["reg_os"].id, cutoff)

    assert result["features"]["attendance_percentage"] is None
    assert result["features"]["classes_held"] is None
    assert result["features"]["mst1_marks"] is None
    assert result["features"]["mst2_marks"] is None
    assert result["features"]["assignment_score"] is None
    assert result["features"]["prior_semesters_completed"] == 0
    assert result["features"]["latest_prior_sgpa"] is None

    # Metadata explicitly lists missing feature groups
    assert "attendance" in result["metadata"]["missing_feature_groups"]
    assert "formative" in result["metadata"]["missing_feature_groups"]


# ===========================================================================
# 14. Deterministic Feature Extraction for Identical Inputs
# ===========================================================================

def test_deterministic_feature_extraction_for_identical_inputs(session, mca_environment):
    """
    Test 14: Verify identical inputs produce deterministic, identical outputs.
    """
    env = mca_environment
    cutoff = datetime(2025, 9, 20, 12, 0, 0)

    session.add(MCAAttendanceSnapshot(
        registration_id=env["reg_os"].id,
        revision_number=1,
        recorded_at=datetime(2025, 9, 15, 10, 0, 0),
        attendance_percentage=Decimal("88.00"),
    ))
    session.add(MCAFormativeSnapshot(
        registration_id=env["reg_os"].id,
        revision_number=1,
        recorded_at=datetime(2025, 9, 15, 11, 0, 0),
        mst1_marks=Decimal("16.00"),
    ))
    session.commit()

    run1 = extract_subject_academic_features(session, env["reg_os"].id, cutoff)
    run2 = extract_subject_academic_features(session, env["reg_os"].id, cutoff)

    assert run1["features"] == run2["features"]
    assert run1["metadata"]["cutoff_timestamp"] == run2["metadata"]["cutoff_timestamp"]
    assert run1["metadata"]["included_snapshots"] == run2["metadata"]["included_snapshots"]


# ===========================================================================
# 15. Successful Prediction Persistence
# ===========================================================================

def test_successful_prediction_persistence(session, mca_environment):
    """
    Test 15: Verify persist_mca_prediction successfully writes a valid
    record into mca_prediction_records.
    """
    env = mca_environment
    cutoff = datetime(2025, 10, 1, 12, 0, 0)

    features_payload = extract_subject_academic_features(session, env["reg_os"].id, cutoff)

    prediction = persist_mca_prediction(
        session=session,
        student_id=env["student"].id,
        registration_id=env["reg_os"].id,
        course_id=env["course_os"].id,
        predicted_tier="Good",
        model_name="mca_subject_rf_v1",
        model_version="1.0.0",
        cutoff_timestamp=cutoff,
        input_snapshot_json=features_payload,
        prediction_probabilities_json={"Good": 0.72, "Average": 0.28},
        commit=True,
    )

    assert prediction.id is not None
    assert prediction.predicted_tier == "Good"
    assert prediction.model_name == "mca_subject_rf_v1"
    assert prediction.model_version == "1.0.0"
    assert prediction.student_id == env["student"].id
    assert prediction.registration_id == env["reg_os"].id
    assert prediction.course_id == env["course_os"].id
    assert prediction.prediction_probabilities_json["Good"] == 0.72

    # Query directly from database
    persisted = get_mca_prediction_by_id(session, prediction.id)
    assert persisted is not None
    assert persisted.predicted_tier == "Good"


# ===========================================================================
# 16. Multiple Predictions Remain Independently Stored
# ===========================================================================

def test_multiple_predictions_remain_independently_stored(session, mca_environment):
    """
    Test 16: Verify persisting multiple predictions creates separate historical
    rows without overwriting or updating prior records.
    """
    env = mca_environment
    cutoff1 = datetime(2025, 9, 15, 12, 0, 0)
    cutoff2 = datetime(2025, 10, 15, 12, 0, 0)

    pred1 = persist_mca_prediction(
        session=session,
        student_id=env["student"].id,
        registration_id=env["reg_os"].id,
        course_id=env["course_os"].id,
        predicted_tier="Average",
        model_name="mca_early_warning",
        cutoff_timestamp=cutoff1,
        input_snapshot_json={"test": "early"},
        commit=True,
    )

    pred2 = persist_mca_prediction(
        session=session,
        student_id=env["student"].id,
        registration_id=env["reg_os"].id,
        course_id=env["course_os"].id,
        predicted_tier="Good",
        model_name="mca_mid_term",
        cutoff_timestamp=cutoff2,
        input_snapshot_json={"test": "midterm"},
        commit=True,
    )

    assert pred1.id != pred2.id
    history = list_mca_predictions_by_registration(session, env["reg_os"].id)
    assert len(history) == 2
    tiers = {p.predicted_tier for p in history}
    assert tiers == {"Average", "Good"}


# ===========================================================================
# 17. Exact Cutoff Timestamp Preservation
# ===========================================================================

def test_exact_cutoff_timestamp_preservation(session, mca_environment):
    """
    Test 17: Verify exact cutoff timestamp is preserved with microsecond fidelity.
    """
    env = mca_environment
    exact_cutoff = datetime(2025, 10, 15, 14, 30, 45, 123456)

    prediction = persist_mca_prediction(
        session=session,
        student_id=env["student"].id,
        registration_id=env["reg_os"].id,
        course_id=env["course_os"].id,
        predicted_tier="Excellent",
        model_name="mca_test_model",
        cutoff_timestamp=exact_cutoff,
        input_snapshot_json={"cutoff_test": True},
        commit=True,
    )

    persisted = get_mca_prediction_by_id(session, prediction.id)
    assert persisted.cutoff_timestamp == exact_cutoff


# ===========================================================================
# 18. Transaction Rollback on Persistence Failure
# ===========================================================================

def test_transaction_rollback_on_persistence_failure(session, mca_environment):
    """
    Test 18: Verify transaction rollback occurs when invalid payload is supplied
    and no partial data persists.
    """
    env = mca_environment
    initial_count = session.query(MCAPredictionRecord).count()

    # Invalid predicted_tier must raise InvalidPredictionPayloadError and rollback
    with pytest.raises(InvalidPredictionPayloadError):
        persist_mca_prediction(
            session=session,
            student_id=env["student"].id,
            predicted_tier="INVALID_TIER",  # Invalid
            model_name="model",
            cutoff_timestamp=datetime(2025, 10, 1),
            input_snapshot_json={"x": 1},
            commit=True,
        )

    assert session.query(MCAPredictionRecord).count() == initial_count


# ===========================================================================
# 19. Foreign Key & Nullability Rules Respected
# ===========================================================================

def test_foreign_key_and_nullability_rules_respected(session, mca_environment):
    """
    Test 19: Verify semester-level predictions (registration_id=None, course_id=None)
    and anonymous predictions (student_id=None) are supported.
    """
    env = mca_environment
    cutoff = datetime(2025, 10, 1)

    # Semester-level prediction: registration_id=None, course_id=None
    sem_pred = persist_mca_prediction(
        session=session,
        student_id=env["student"].id,
        registration_id=None,
        course_id=None,
        predicted_tier="Good",
        model_name="mca_semester_model",
        cutoff_timestamp=cutoff,
        input_snapshot_json={"scope": "semester"},
        commit=True,
    )
    assert sem_pred.id is not None
    assert sem_pred.registration_id is None
    assert sem_pred.course_id is None
    assert sem_pred.student_id == env["student"].id

    # Anonymous prediction: student_id=None, registration_id=None, course_id=None
    anon_pred = persist_mca_prediction(
        session=session,
        student_id=None,
        registration_id=None,
        course_id=None,
        predicted_tier="Average",
        model_name="mca_anon_eval",
        cutoff_timestamp=cutoff,
        input_snapshot_json={"scope": "anonymous"},
        commit=True,
    )
    assert anon_pred.id is not None
    assert anon_pred.student_id is None


# ===========================================================================
# 20. Phase 1 UCI Infrastructure Unaffected
# ===========================================================================

def test_phase1_uci_infrastructure_unaffected(session, mca_environment):
    """
    Test 20: Verify Phase 1 UCI models (Student, PredictionRecord) remain
    completely functional alongside Phase 2E feature extraction and persistence.
    """
    env = mca_environment

    # 1. Add Phase 1 UCI Student
    uci_student = Student(student_code="UCI-STUDENT-999")
    session.add(uci_student)
    session.commit()

    # 2. Add Phase 1 UCI PredictionRecord
    uci_pred = PredictionRecord(
        student_id=uci_student.id,
        subject="Mathematics",
        scenario="Scenario A",
        model_name="uci_logistic_regression",
        model_version="1.0.0",
        predicted_category="Good",
        input_features={"studytime": 2, "failures": 0},
        recommendations={"strengths": ["Consistent study habits"]},
    )
    session.add(uci_pred)
    session.commit()

    # 3. Add Phase 2E MCA Prediction
    mca_pred = persist_mca_prediction(
        session=session,
        student_id=env["student"].id,
        registration_id=env["reg_os"].id,
        course_id=env["course_os"].id,
        predicted_tier="Excellent",
        model_name="mca_gradient_boost",
        cutoff_timestamp=datetime(2025, 10, 1),
        input_snapshot_json={"academic": "features"},
        commit=True,
    )

    # 4. Verify both coexist independently
    assert session.get(Student, uci_student.id).student_code == "UCI-STUDENT-999"
    assert session.get(PredictionRecord, uci_pred.id).subject == "Mathematics"
    assert session.get(MCAPredictionRecord, mca_pred.id).predicted_tier == "Excellent"
    assert session.query(PredictionRecord).count() >= 1
    assert session.query(MCAPredictionRecord).count() >= 1
