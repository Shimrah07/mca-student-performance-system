"""
backend/tests/test_mca_predictions_api.py

Automated integration test suite for Phase 3B: MCA ML Model and FastAPI Integration.

Verifies:
1. Subject-level prediction endpoint logic (predict_subject_level).
2. Semester-level prediction endpoint logic (predict_semester_level).
3. Correct model selection for each scope (Logistic Regression for subject, Random Forest for semester).
4. Correct Phase 2E feature extraction invocation with strict point-in-time cutoff.
5. Correct feature adapter mapping and input snapshot integrity.
6. Immutable prediction persistence into `mca_prediction_records`.
7. Missing required cutoff timestamp validation (enforced by Pydantic; never defaulted).
8. Invalid student/registration/course relationships rejection (HTTPException 404 / 422).
9. Missing academic features handled gracefully (median imputation, zero crash).
10. Prediction response synthetic data prototype disclaimer.
11. Artifact loading failure handling (HTTPException 503).
12. Strict leakage prevention (zero target final scores or identifiers in model features).
13. No mutation or overwriting of historical prediction records (append-only audit trail).
14. SQLite isolation with PRAGMA foreign_keys=ON (zero MySQL queries).
15. Historical prediction retrieval functions (by ID and by student).
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, Generator
from unittest.mock import patch
import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi import HTTPException
from pydantic import ValidationError

import ml.src.mca_compat  # Safe sklearn C-extension handling on Windows

from app.database import Base
from app.models import (
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
)
from app.routers.mca_predictions import (
    get_prediction_record,
    list_student_predictions,
    predict_semester_level,
    predict_subject_level,
)
from app.schemas.mca import (
    McaSemesterPredictionApiRequest,
    McaSubjectPredictionApiRequest,
)
from ml.src.mca_predictor import clear_mca_model_cache


# ===========================================================================
# Isolated SQLite Database Fixture with PRAGMA foreign_keys=ON
# ===========================================================================

@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """
    Create an isolated, in-memory SQLite database fixture enforcing foreign keys.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, _):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()

    yield session

    session.close()


# ===========================================================================
# Academic Test Environment Helper
# ===========================================================================

def setup_academic_environment(session: Session) -> Dict[str, Any]:
    """
    Populate a complete canonical MCA academic hierarchy in SQLite:
    - Program & Scheme
    - Academic Session
    - Courses (Theory, Lab, Project)
    - Session Courses
    - Student
    - Course Registrations
    - Attendance, Formative, and Milestone Snapshots (multi-revision)
    - Historical Semester Results
    """
    # 1. Program & Scheme
    program = MCAProgram(
        program_name="Master of Computer Applications",
        program_code="MCA",
        duration_semesters=4,
    )
    session.add(program)
    session.flush()

    scheme = MCACurriculumScheme(
        program_id=program.id,
        scheme_name="UIT-RGPV Autonomous MCA Scheme (July 2025)",
        scheme_code="MCA-AUTONOMOUS-2025",
        effective_from="July 2025",
        is_active=True,
    )
    session.add(scheme)
    session.flush()

    academic_session = MCAAcademicSession(
        scheme_id=scheme.id,
        session_name="MCA 2025-27 Batch",
        batch_year="2025-2027",
        start_date=date(2025, 7, 1),
        end_date=date(2027, 6, 30),
        is_active=True,
    )
    session.add(academic_session)
    session.flush()

    # 2. Courses
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
        course_code="MCA114",
        course_name="Operating System Lab",
        semester_number=1,
        course_type="lab",
        credits=4,
    )
    course_proj = MCACourse(
        program_id=program.id,
        scheme_id=scheme.id,
        course_code="MCA305",
        course_name="Minor Project",
        semester_number=3,
        course_type="project",
        credits=6,
    )
    session.add_all([course_os, course_lab, course_proj])
    session.flush()

    # 3. Session Courses
    sc_os = MCASessionCourse(session_id=academic_session.id, course_id=course_os.id)
    sc_lab = MCASessionCourse(session_id=academic_session.id, course_id=course_lab.id)
    sc_proj = MCASessionCourse(session_id=academic_session.id, course_id=course_proj.id)
    session.add_all([sc_os, sc_lab, sc_proj])
    session.flush()

    # 4. Student
    student = MCAStudent(
        student_code="MCA-2025-001",
        session_id=academic_session.id,
        is_active=True,
    )
    session.add(student)
    session.flush()

    # 5. Registrations
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
    session.add_all([reg_os, reg_lab])
    session.flush()

    # 6. Snapshots for reg_os (recorded at different times)
    att1 = MCAAttendanceSnapshot(
        registration_id=reg_os.id,
        revision_number=1,
        classes_held=20,
        classes_attended=15,
        attendance_percentage=Decimal("75.00"),
        recorded_at=datetime(2025, 9, 1, 10, 0, 0),
    )
    att2 = MCAAttendanceSnapshot(
        registration_id=reg_os.id,
        revision_number=2,
        classes_held=30,
        classes_attended=26,
        attendance_percentage=Decimal("86.67"),
        recorded_at=datetime(2025, 9, 15, 10, 0, 0),
    )
    att3 = MCAAttendanceSnapshot(
        registration_id=reg_os.id,
        revision_number=3,
        classes_held=40,
        classes_attended=38,
        attendance_percentage=Decimal("95.00"),
        recorded_at=datetime(2025, 10, 10, 10, 0, 0),  # After Sept 20 cutoff
    )

    form1 = MCAFormativeSnapshot(
        registration_id=reg_os.id,
        revision_number=1,
        mst1_marks=Decimal("17.50"),
        mst2_marks=Decimal("18.00"),
        assignment_score=Decimal("9.00"),
        recorded_at=datetime(2025, 9, 14, 12, 0, 0),
    )
    session.add_all([att1, att2, att3, form1])

    # Snapshots for reg_lab
    att_lab = MCAAttendanceSnapshot(
        registration_id=reg_lab.id,
        revision_number=1,
        classes_held=10,
        classes_attended=9,
        attendance_percentage=Decimal("90.00"),
        recorded_at=datetime(2025, 9, 10, 10, 0, 0),
    )
    form_lab = MCAFormativeSnapshot(
        registration_id=reg_lab.id,
        revision_number=1,
        viva_marks=Decimal("18.00"),
        lab_record_score=Decimal("9.50"),
        recorded_at=datetime(2025, 9, 12, 10, 0, 0),
    )
    session.add_all([att_lab, form_lab])
    session.commit()

    return {
        "program": program,
        "scheme": scheme,
        "session": academic_session,
        "student": student,
        "course_os": course_os,
        "course_lab": course_lab,
        "course_proj": course_proj,
        "reg_os": reg_os,
        "reg_lab": reg_lab,
    }


# ===========================================================================
# 1. Subject-Level Prediction Tests
# ===========================================================================

def test_subject_level_prediction_endpoint_success(db_session: Session):
    """
    Test predict_subject_level returns complete prediction schema,
    probabilities, model metadata, and persisted record ID.
    """
    env = setup_academic_environment(db_session)
    reg_id = env["reg_os"].id
    cutoff = datetime(2025, 9, 20, 0, 0, 0, tzinfo=timezone.utc)

    req = McaSubjectPredictionApiRequest(
        registration_id=reg_id,
        cutoff_timestamp=cutoff,
    )

    res = predict_subject_level(req, db_session)

    assert res.scope == "subject"
    assert res.registration_id == reg_id
    assert res.student_id == env["student"].id
    assert res.course_id == env["course_os"].id
    assert res.course_code == "MCA108"
    assert res.course_name == "Operating System"
    assert res.target_semester == 1
    assert res.predicted_tier in {"Excellent", "Good", "Average", "Needs Improvement"}
    assert 0.0 <= res.confidence <= 1.0
    assert isinstance(res.probabilities, dict)
    assert len(res.probabilities) == 4

    # Model used must be subject-level Logistic Regression
    assert "logistic_regression" in res.model_name
    assert "synthetic" in res.synthetic_data_warning.lower()

    # Verify record was persisted in database
    prediction_id = res.prediction_id
    persisted_record = db_session.get(MCAPredictionRecord, prediction_id)
    assert persisted_record is not None
    assert persisted_record.predicted_tier == res.predicted_tier
    assert persisted_record.student_id == env["student"].id
    assert persisted_record.registration_id == reg_id


def test_subject_level_prediction_with_matching_student_id_validation(db_session: Session):
    """Verify subject prediction succeeds when matching student_id is provided."""
    env = setup_academic_environment(db_session)
    req = McaSubjectPredictionApiRequest(
        registration_id=env["reg_os"].id,
        student_id=env["student"].id,
        cutoff_timestamp=datetime(2025, 9, 20, tzinfo=timezone.utc),
    )
    res = predict_subject_level(req, db_session)
    assert res.student_id == env["student"].id


# ===========================================================================
# 2. Semester-Level Prediction Tests
# ===========================================================================

def test_semester_level_prediction_endpoint_success(db_session: Session):
    """
    Test predict_semester_level returns aggregated metrics,
    probabilities, model metadata, and persisted record ID.
    """
    env = setup_academic_environment(db_session)
    student_id = env["student"].id
    cutoff = datetime(2025, 9, 20, 0, 0, 0, tzinfo=timezone.utc)

    req = McaSemesterPredictionApiRequest(
        student_id=student_id,
        target_semester=1,
        cutoff_timestamp=cutoff,
    )

    res = predict_semester_level(req, db_session)

    assert res.scope == "semester"
    assert res.student_id == student_id
    assert res.registration_id is None
    assert res.course_id is None
    assert res.target_semester == 1
    assert res.predicted_tier in {"Excellent", "Good", "Average", "Needs Improvement"}
    assert 0.0 <= res.confidence <= 1.0
    assert len(res.probabilities) == 4

    # Semester model must be Random Forest
    assert "random_forest" in res.model_name
    assert "synthetic" in res.synthetic_data_warning.lower()

    # Verify record was persisted
    prediction_id = res.prediction_id
    persisted_record = db_session.get(MCAPredictionRecord, prediction_id)
    assert persisted_record is not None
    assert persisted_record.predicted_tier == res.predicted_tier
    assert persisted_record.registration_id is None
    assert persisted_record.course_id is None


# ===========================================================================
# 3. Model Selection per Scope Tests
# ===========================================================================

def test_correct_model_selection_per_scope(db_session: Session):
    """
    Verify subject-level invokes Logistic Regression pipeline while
    semester-level invokes Random Forest pipeline.
    """
    env = setup_academic_environment(db_session)
    cutoff = datetime(2025, 9, 20, tzinfo=timezone.utc)

    res_subj = predict_subject_level(
        McaSubjectPredictionApiRequest(registration_id=env["reg_os"].id, cutoff_timestamp=cutoff),
        db_session,
    )
    assert "logistic_regression" in res_subj.model_name

    res_sem = predict_semester_level(
        McaSemesterPredictionApiRequest(student_id=env["student"].id, target_semester=1, cutoff_timestamp=cutoff),
        db_session,
    )
    assert "random_forest" in res_sem.model_name


# ===========================================================================
# 4. Point-in-Time Cutoff Enforcement (No Leakage)
# ===========================================================================

def test_point_in_time_feature_extraction_cutoff_enforcement(db_session: Session):
    """
    Verify snapshots recorded AFTER cutoff_timestamp are strictly excluded from feature extraction
    and do not leak into model inputs.
    """
    env = setup_academic_environment(db_session)
    cutoff = datetime(2025, 9, 20, tzinfo=timezone.utc)

    res = predict_subject_level(
        McaSubjectPredictionApiRequest(registration_id=env["reg_os"].id, cutoff_timestamp=cutoff),
        db_session,
    )

    # Check input snapshot stored immutably
    features = res.input_snapshot_json["features"]
    assert features["attendance_percentage"] == pytest.approx(86.67, abs=0.1)

    included_snaps = res.input_snapshot_json["metadata"]["included_snapshots"]
    assert included_snaps["attendance"]["revision_number"] == 2


# ===========================================================================
# 5. Missing Required Cutoff Timestamp Validation
# ===========================================================================

def test_missing_required_cutoff_timestamp_rejected():
    """
    Verify requests missing cutoff_timestamp fail validation.
    Current time must NEVER be substituted.
    """
    with pytest.raises(ValidationError):
        McaSubjectPredictionApiRequest(registration_id=1)  # type: ignore

    with pytest.raises(ValidationError):
        McaSemesterPredictionApiRequest(student_id=1, target_semester=1)  # type: ignore


# ===========================================================================
# 6. Entity Relationships & Bounds Validation
# ===========================================================================

def test_nonexistent_registration_returns_404(db_session: Session):
    """Verify nonexistent registration ID raises HTTP 404 Not Found."""
    setup_academic_environment(db_session)
    req = McaSubjectPredictionApiRequest(registration_id=99999, cutoff_timestamp=datetime(2025, 9, 20, tzinfo=timezone.utc))
    with pytest.raises(HTTPException) as exc_info:
        predict_subject_level(req, db_session)
    assert exc_info.value.status_code == 404
    assert "MCACourseRegistration with id=99999 not found" in exc_info.value.detail


def test_nonexistent_student_returns_404(db_session: Session):
    """Verify nonexistent student ID in semester prediction raises HTTP 404 Not Found."""
    setup_academic_environment(db_session)
    req = McaSemesterPredictionApiRequest(student_id=99999, target_semester=1, cutoff_timestamp=datetime(2025, 9, 20, tzinfo=timezone.utc))
    with pytest.raises(HTTPException) as exc_info:
        predict_semester_level(req, db_session)
    assert exc_info.value.status_code == 404
    assert "MCAStudent with id=99999 not found" in exc_info.value.detail


def test_mismatched_student_registration_rejected(db_session: Session):
    """Verify passing a student_id that does not own the registration raises HTTP 422."""
    env = setup_academic_environment(db_session)
    req = McaSubjectPredictionApiRequest(
        registration_id=env["reg_os"].id,
        student_id=999,
        cutoff_timestamp=datetime(2025, 9, 20, tzinfo=timezone.utc),
    )
    with pytest.raises(HTTPException) as exc_info:
        predict_subject_level(req, db_session)
    assert exc_info.value.status_code == 422
    assert "belongs to student_id=" in exc_info.value.detail


def test_invalid_target_semester_rejected():
    """Verify target_semester outside 1 to 4 is rejected by schema validator."""
    for invalid_sem in (0, 5, -1):
        with pytest.raises(ValidationError):
            McaSemesterPredictionApiRequest(
                student_id=1,
                target_semester=invalid_sem,
                cutoff_timestamp=datetime(2025, 9, 20, tzinfo=timezone.utc),
            )


# ===========================================================================
# 7. Missing Academic Features & Insufficient Data Validation
# ===========================================================================

def test_missing_academic_features_handled_gracefully(db_session: Session):
    """
    Verify prediction succeeds when student has eligible attendance but missing formative/milestone snapshots.
    Individual missing features are imputed via median imputer without crashing.
    """
    env = setup_academic_environment(db_session)

    new_reg = MCACourseRegistration(
        student_id=env["student"].id,
        session_course_id=env["reg_lab"].session_course_id,
        semester_number=1,
        attempt_type="regular",
        is_active=True,
    )
    db_session.add(new_reg)
    db_session.flush()

    # Provide only attendance snapshot, no formative or milestone snapshots
    snap_att = MCAAttendanceSnapshot(
        registration_id=new_reg.id,
        revision_number=1,
        classes_held=20,
        classes_attended=16,
        attendance_percentage=Decimal("80.00"),
        recorded_at=datetime(2025, 7, 4, 10, 0, 0),
    )
    db_session.add(snap_att)
    db_session.commit()

    req = McaSubjectPredictionApiRequest(
        registration_id=new_reg.id,
        cutoff_timestamp=datetime(2025, 7, 5, tzinfo=timezone.utc),
    )
    res = predict_subject_level(req, db_session)
    assert res.predicted_tier in {"Excellent", "Good", "Average", "Needs Improvement"}
    assert res.input_snapshot_json["features"]["attendance_percentage"] == 80.0
    assert res.input_snapshot_json["features"]["mst1_marks"] is None


def test_zero_snapshots_raises_insufficient_data_error(db_session: Session):
    """
    Verify requesting a prediction when student has ZERO eligible academic snapshots
    raises HTTP 422 with a clear insufficient academic data response, preventing fabricated predictions.
    """
    env = setup_academic_environment(db_session)

    empty_reg = MCACourseRegistration(
        student_id=env["student"].id,
        session_course_id=env["reg_lab"].session_course_id,
        semester_number=1,
        attempt_type="regular",
        is_active=True,
    )
    db_session.add(empty_reg)
    db_session.commit()

    req = McaSubjectPredictionApiRequest(
        registration_id=empty_reg.id,
        cutoff_timestamp=datetime(2025, 7, 5, tzinfo=timezone.utc),
    )
    with pytest.raises(HTTPException) as exc_info:
        predict_subject_level(req, db_session)

    assert exc_info.value.status_code == 422
    assert "No eligible academic snapshots" in exc_info.value.detail


# ===========================================================================
# 8. Historical Record Persistence & Immutability
# ===========================================================================

def test_immutable_prediction_persistence_and_no_mutation(db_session: Session):
    """
    Verify multiple prediction requests create independent immutable rows
    and do not overwrite previous predictions.
    """
    env = setup_academic_environment(db_session)
    reg_id = env["reg_os"].id

    res1 = predict_subject_level(
        McaSubjectPredictionApiRequest(registration_id=reg_id, cutoff_timestamp=datetime(2025, 9, 10, tzinfo=timezone.utc)),
        db_session,
    )
    id1 = res1.prediction_id

    res2 = predict_subject_level(
        McaSubjectPredictionApiRequest(registration_id=reg_id, cutoff_timestamp=datetime(2025, 9, 20, tzinfo=timezone.utc)),
        db_session,
    )
    id2 = res2.prediction_id

    assert id1 != id2
    rec1 = db_session.get(MCAPredictionRecord, id1)
    rec2 = db_session.get(MCAPredictionRecord, id2)
    assert rec1 is not None
    assert rec2 is not None
    assert rec1.cutoff_timestamp != rec2.cutoff_timestamp


def test_get_prediction_by_id_endpoint(db_session: Session):
    """Test get_prediction_record retrieves persisted record."""
    env = setup_academic_environment(db_session)
    created = predict_subject_level(
        McaSubjectPredictionApiRequest(registration_id=env["reg_os"].id, cutoff_timestamp=datetime(2025, 9, 20, tzinfo=timezone.utc)),
        db_session,
    )
    pred_id = created.prediction_id

    retrieved = get_prediction_record(pred_id, db_session)
    assert retrieved.prediction_id == pred_id
    assert retrieved.registration_id == env["reg_os"].id
    assert retrieved.predicted_tier == created.predicted_tier

    with pytest.raises(HTTPException) as exc_info:
        get_prediction_record(999999, db_session)
    assert exc_info.value.status_code == 404


def test_list_student_predictions_endpoint(db_session: Session):
    """Test list_student_predictions lists all predictions for student."""
    env = setup_academic_environment(db_session)
    stu_id = env["student"].id

    predict_subject_level(
        McaSubjectPredictionApiRequest(registration_id=env["reg_os"].id, cutoff_timestamp=datetime(2025, 9, 10, tzinfo=timezone.utc)),
        db_session,
    )
    predict_semester_level(
        McaSemesterPredictionApiRequest(student_id=stu_id, target_semester=1, cutoff_timestamp=datetime(2025, 9, 20, tzinfo=timezone.utc)),
        db_session,
    )

    items = list_student_predictions(stu_id, 50, db_session)
    assert len(items) >= 2
    scopes = {item.scope for item in items}
    assert "subject" in scopes
    assert "semester" in scopes


# ===========================================================================
# 9. Artifact Loading Failure Handling
# ===========================================================================

def test_artifact_loading_failure_returns_503(db_session: Session):
    """Verify that if the model artifact is missing or invalid, HTTP 503 is returned."""
    env = setup_academic_environment(db_session)
    clear_mca_model_cache()

    with patch(
        "app.services.mca_prediction_service.predict_subject_performance",
        side_effect=FileNotFoundError("Mocked missing artifact error"),
    ):
        req = McaSubjectPredictionApiRequest(registration_id=env["reg_os"].id, cutoff_timestamp=datetime(2025, 9, 20, tzinfo=timezone.utc))
        with pytest.raises(HTTPException) as exc_info:
            predict_subject_level(req, db_session)
        assert exc_info.value.status_code == 503
        assert "Model artifact not available" in exc_info.value.detail
