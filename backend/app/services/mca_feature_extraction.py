"""
backend/app/services/mca_feature_extraction.py

MCA Academic Feature Extraction Service.
Extracts point-in-time academic feature snapshots with strict temporal cutoff enforcement,
preventing data leakage and handling missing academic data deterministically.

Adheres strictly to Phase2B_Final_Implementation_Contract.md:
- Attendance snapshots: recorded_at <= cutoff_timestamp, latest revision selected.
- Formative snapshots: recorded_at <= cutoff_timestamp, latest revision selected.
- Project milestone snapshots: recorded_at <= cutoff_timestamp, latest revision selected.
- Historical semester results:
    * semester_number < target_semester (strict predecessor)
    * declared_at IS NOT NULL
    * declared_at <= cutoff_timestamp
    * recorded_at <= cutoff_timestamp
- Target semester results and future assessments are strictly excluded (no data leakage).
- Missing academic data is explicitly preserved as None (no fabricated values).
- Supports distinct subject-level and semester-level prediction scopes.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional, Set

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    MCAAttendanceSnapshot,
    MCACourse,
    MCACourseRegistration,
    MCAFormativeSnapshot,
    MCAProjectMilestoneSnapshot,
    MCASemesterResult,
    MCASessionCourse,
    MCAStudent,
)

logger = logging.getLogger("mca_feature_extraction")


# ===========================================================================
# Exceptions
# ===========================================================================

class FeatureExtractionError(Exception):
    """Base exception for feature extraction failures."""
    pass


class InvalidCutoffTimestampError(FeatureExtractionError):
    """Raised when cutoff_timestamp is missing, invalid, or improperly formatted."""
    pass


class InvalidPredictionScopeError(FeatureExtractionError):
    """Raised when prediction scope is invalid or incompatible arguments are supplied."""
    pass


class EntityNotFoundError(FeatureExtractionError):
    """Raised when a requested student, course registration, or course cannot be found."""
    pass


class InsufficientAcademicDataError(FeatureExtractionError):
    """Raised when no eligible academic snapshots exist at or before the cutoff timestamp."""
    pass


# ===========================================================================
# Utility Helpers
# ===========================================================================

def _validate_and_normalize_cutoff(cutoff_timestamp: Any) -> datetime:
    """
    Validate and normalize the caller-supplied cutoff timestamp.
    Enforces that cutoff_timestamp is an explicit datetime instance.
    Never substitutes current system time.
    """
    if cutoff_timestamp is None:
        raise InvalidCutoffTimestampError(
            "cutoff_timestamp is required and cannot be None. "
            "System time must never be substituted for an explicit cutoff."
        )
    if not isinstance(cutoff_timestamp, datetime):
        raise InvalidCutoffTimestampError(
            f"cutoff_timestamp must be a datetime instance, got {type(cutoff_timestamp).__name__}."
        )

    # Normalize tzinfo: if aware, convert to UTC and make naive for consistent DB comparison
    if cutoff_timestamp.tzinfo is not None:
        return cutoff_timestamp.astimezone(timezone.utc).replace(tzinfo=None)
    return cutoff_timestamp


# ===========================================================================
# Point-in-Time Snapshot Extractors (Single Registration)
# ===========================================================================

def _extract_latest_attendance_snapshot(
    session: Session,
    registration_id: int,
    cutoff: datetime,
) -> Optional[MCAAttendanceSnapshot]:
    """
    Fetch the latest eligible attendance snapshot revision recorded at or before cutoff.
    Revisions with recorded_at > cutoff are strictly excluded.
    """
    stmt = (
        select(MCAAttendanceSnapshot)
        .where(
            MCAAttendanceSnapshot.registration_id == registration_id,
            MCAAttendanceSnapshot.recorded_at <= cutoff,
        )
        .order_by(MCAAttendanceSnapshot.revision_number.desc())
        .limit(1)
    )
    return session.execute(stmt).scalar_one_or_none()


def _extract_latest_formative_snapshot(
    session: Session,
    registration_id: int,
    cutoff: datetime,
) -> Optional[MCAFormativeSnapshot]:
    """
    Fetch the latest eligible formative snapshot revision recorded at or before cutoff.
    Revisions with recorded_at > cutoff are strictly excluded.
    """
    stmt = (
        select(MCAFormativeSnapshot)
        .where(
            MCAFormativeSnapshot.registration_id == registration_id,
            MCAFormativeSnapshot.recorded_at <= cutoff,
        )
        .order_by(MCAFormativeSnapshot.revision_number.desc())
        .limit(1)
    )
    return session.execute(stmt).scalar_one_or_none()


def _extract_latest_milestone_snapshot(
    session: Session,
    registration_id: int,
    cutoff: datetime,
) -> Optional[MCAProjectMilestoneSnapshot]:
    """
    Fetch the latest eligible project milestone snapshot revision recorded at or before cutoff.
    Revisions with recorded_at > cutoff are strictly excluded.
    """
    stmt = (
        select(MCAProjectMilestoneSnapshot)
        .where(
            MCAProjectMilestoneSnapshot.registration_id == registration_id,
            MCAProjectMilestoneSnapshot.recorded_at <= cutoff,
        )
        .order_by(MCAProjectMilestoneSnapshot.revision_number.desc())
        .limit(1)
    )
    return session.execute(stmt).scalar_one_or_none()


# ===========================================================================
# Historical Semester Results Extractor
# ===========================================================================

def _extract_eligible_prior_semester_results(
    session: Session,
    student_id: int,
    target_semester: int,
    cutoff: datetime,
) -> List[MCASemesterResult]:
    """
    Extract eligible finalized semester results for prior semesters.

    Eligibility Rules (Phase2B Section 7):
    1. semester_number < target_semester (strict predecessor, NO target-result leakage)
    2. declared_at IS NOT NULL (provisional/undeclared results excluded)
    3. declared_at <= cutoff (future declarations excluded)
    4. recorded_at <= cutoff (future database insertions excluded)

    If multiple revisions exist for a semester, the latest recorded prior to cutoff is retained.
    """
    stmt = (
        select(MCASemesterResult)
        .where(
            MCASemesterResult.student_id == student_id,
            MCASemesterResult.semester_number < target_semester,
            MCASemesterResult.declared_at.is_not(None),
            MCASemesterResult.declared_at <= cutoff,
            MCASemesterResult.recorded_at <= cutoff,
        )
        .order_by(
            MCASemesterResult.semester_number.asc(),
            MCASemesterResult.recorded_at.desc(),
        )
    )
    rows = session.execute(stmt).scalars().all()

    # Deduplicate by semester_number, preserving latest recorded row
    results_by_semester: Dict[int, MCASemesterResult] = {}
    for r in rows:
        if r.semester_number not in results_by_semester:
            results_by_semester[r.semester_number] = r

    # Return sorted by semester_number
    return [results_by_semester[s] for s in sorted(results_by_semester.keys())]


def _build_prior_results_features(
    prior_results: List[MCASemesterResult],
) -> Dict[str, Any]:
    """
    Build deterministic academic performance features from eligible prior semester results.
    Does not invent grades or CGPA when results are unavailable.
    """
    if not prior_results:
        return {
            "prior_semesters_completed": 0,
            "latest_prior_sgpa": None,
            "cumulative_prior_sgpa_avg": None,
            "latest_declared_cgpa": None,
            "prior_sgpas_by_semester": {},
        }

    sgpas_by_sem = {r.semester_number: float(r.sgpa) for r in prior_results}
    latest_result = prior_results[-1]  # Highest semester number among eligible predecessors

    sgpa_sum = sum(sgpas_by_sem.values())
    sgpa_avg = round(sgpa_sum / len(sgpas_by_sem), 2) if sgpas_by_sem else None

    latest_cgpa = float(latest_result.cgpa) if latest_result.cgpa is not None else None

    return {
        "prior_semesters_completed": len(prior_results),
        "latest_prior_sgpa": float(latest_result.sgpa),
        "cumulative_prior_sgpa_avg": sgpa_avg,
        "latest_declared_cgpa": latest_cgpa,
        "prior_sgpas_by_semester": sgpas_by_sem,
    }


# ===========================================================================
# Subject-Level Feature Extraction
# ===========================================================================

def extract_subject_academic_features(
    session: Session,
    registration_id: int,
    cutoff_timestamp: datetime,
    require_snapshots: bool = False,
) -> Dict[str, Any]:
    """
    Extract point-in-time academic features for a single course registration.

    Scope: Subject-level prediction.
    Features extracted:
    - Course metadata (course_code, course_name, course_type, semester_number).
    - Latest eligible attendance snapshot recorded at or before cutoff.
    - Latest eligible formative snapshot recorded at or before cutoff.
    - Latest eligible project milestone snapshot recorded at or before cutoff.
    - Eligible previous semester examination results (semesters < registration semester).

    Guarantees:
    - Never uses data recorded or declared after cutoff.
    - Never includes final examination results for the target semester.
    - Returns None for missing feature groups (never fabricates attendance or scores).
    """
    cutoff = _validate_and_normalize_cutoff(cutoff_timestamp)

    # 1. Fetch course registration and context
    reg = session.get(MCACourseRegistration, registration_id)
    if reg is None:
        raise EntityNotFoundError(f"MCACourseRegistration with id={registration_id} not found.")

    student = session.get(MCAStudent, reg.student_id)
    if student is None:
        raise EntityNotFoundError(f"MCAStudent with id={reg.student_id} not found for registration={registration_id}.")

    session_course = session.get(MCASessionCourse, reg.session_course_id)
    if session_course is None:
        raise EntityNotFoundError(f"MCASessionCourse with id={reg.session_course_id} not found.")

    course = session.get(MCACourse, session_course.course_id)
    if course is None:
        raise EntityNotFoundError(f"MCACourse with id={session_course.course_id} not found.")

    target_semester = reg.semester_number

    # 2. Extract snapshots
    att_snap = _extract_latest_attendance_snapshot(session, registration_id, cutoff)
    form_snap = _extract_latest_formative_snapshot(session, registration_id, cutoff)
    mile_snap = _extract_latest_milestone_snapshot(session, registration_id, cutoff)

    # Strict validation: At least one point-in-time academic snapshot must exist when require_snapshots=True.
    # Never generate a prediction using invented or hardcoded features.
    if require_snapshots and att_snap is None and form_snap is None and mile_snap is None:
        raise InsufficientAcademicDataError(
            f"No eligible academic snapshots (attendance, formative assessments, or project milestones) "
            f"found for registration_id={registration_id} at or before cutoff timestamp {cutoff.isoformat()}. "
            "A prediction cannot be generated without at least one point-in-time academic snapshot."
        )

    # 3. Extract eligible prior semester results
    prior_results = _extract_eligible_prior_semester_results(session, student.id, target_semester, cutoff)

    # 4. Track included sources and missing feature groups
    missing_groups: List[str] = []
    included_snapshots: Dict[str, Optional[Dict[str, Any]]] = {}

    if att_snap is not None:
        included_snapshots["attendance"] = {
            "snapshot_id": att_snap.id,
            "revision_number": att_snap.revision_number,
            "recorded_at": att_snap.recorded_at.isoformat() if att_snap.recorded_at else None,
        }
    else:
        included_snapshots["attendance"] = None
        missing_groups.append("attendance")

    if form_snap is not None:
        included_snapshots["formative"] = {
            "snapshot_id": form_snap.id,
            "revision_number": form_snap.revision_number,
            "recorded_at": form_snap.recorded_at.isoformat() if form_snap.recorded_at else None,
        }
    else:
        included_snapshots["formative"] = None
        missing_groups.append("formative")

    if mile_snap is not None:
        included_snapshots["milestone"] = {
            "snapshot_id": mile_snap.id,
            "revision_number": mile_snap.revision_number,
            "recorded_at": mile_snap.recorded_at.isoformat() if mile_snap.recorded_at else None,
        }
    else:
        included_snapshots["milestone"] = None
        if course.course_type == "project":
            missing_groups.append("milestone")

    if not prior_results and target_semester > 1:
        missing_groups.append("prior_semester_results")

    # 5. Assemble features dictionary
    prior_features = _build_prior_results_features(prior_results)

    features = {
        # Attendance features
        "attendance_percentage": float(att_snap.attendance_percentage) if att_snap and att_snap.attendance_percentage is not None else None,
        "classes_held": att_snap.classes_held if att_snap else None,
        "classes_attended": att_snap.classes_attended if att_snap else None,
        # Formative features
        "mst1_marks": float(form_snap.mst1_marks) if form_snap and form_snap.mst1_marks is not None else None,
        "mst2_marks": float(form_snap.mst2_marks) if form_snap and form_snap.mst2_marks is not None else None,
        "assignment_score": float(form_snap.assignment_score) if form_snap and form_snap.assignment_score is not None else None,
        "viva_marks": float(form_snap.viva_marks) if form_snap and form_snap.viva_marks is not None else None,
        "lab_record_score": float(form_snap.lab_record_score) if form_snap and form_snap.lab_record_score is not None else None,
        # Milestone features
        "synopsis_approved": mile_snap.synopsis_approved if mile_snap else None,
        "design_score": float(mile_snap.design_score) if mile_snap and mile_snap.design_score is not None else None,
        "implementation_pct": float(mile_snap.implementation_pct) if mile_snap and mile_snap.implementation_pct is not None else None,
        "supervisor_score": float(mile_snap.supervisor_score) if mile_snap and mile_snap.supervisor_score is not None else None,
        # Historical academic performance features
        **prior_features,
    }

    # 6. Assemble metadata dictionary
    metadata = {
        "student_id": student.id,
        "student_code": student.student_code,
        "prediction_scope": "subject",
        "target_semester": target_semester,
        "registration_id": reg.id,
        "attempt_type": reg.attempt_type,
        "course_id": course.id,
        "course_code": course.course_code,
        "course_name": course.course_name,
        "course_type": course.course_type,
        "credits": course.credits,
        "cutoff_timestamp": cutoff.isoformat(),
        "included_snapshots": included_snapshots,
        "included_semester_results": [
            {
                "id": r.id,
                "semester_number": r.semester_number,
                "sgpa": float(r.sgpa),
                "cgpa": float(r.cgpa) if r.cgpa is not None else None,
                "declared_at": r.declared_at.isoformat() if r.declared_at else None,
                "recorded_at": r.recorded_at.isoformat() if r.recorded_at else None,
            }
            for r in prior_results
        ],
        "missing_feature_groups": missing_groups,
    }

    return {
        "metadata": metadata,
        "features": features,
    }


# ===========================================================================
# Semester-Level Feature Extraction
# ===========================================================================

def extract_semester_academic_features(
    session: Session,
    student_id: int,
    target_semester: int,
    cutoff_timestamp: datetime,
    require_snapshots: bool = False,
) -> Dict[str, Any]:
    """
    Extract point-in-time academic features for an entire target semester of a student.

    Scope: Semester-level prediction.
    Features extracted:
    - All active course registrations of the student in the target semester.
    - For each course: latest eligible attendance, formative, and milestone snapshots.
    - Aggregated cohort-level features (average attendance, min attendance, formative averages).
    - Eligible previous semester examination results (semesters < target_semester).

    Guarantees:
    - Never uses data recorded or declared after cutoff.
    - Never includes final examination results for the target semester.
    - Returns None for missing feature groups (never fabricates attendance or scores).
    """
    cutoff = _validate_and_normalize_cutoff(cutoff_timestamp)

    if target_semester not in (1, 2, 3, 4):
        raise InvalidPredictionScopeError(
            f"target_semester must be an integer between 1 and 4, got {target_semester}."
        )

    student = session.get(MCAStudent, student_id)
    if student is None:
        raise EntityNotFoundError(f"MCAStudent with id={student_id} not found.")

    # 1. Fetch all active course registrations for the student in target semester
    stmt = (
        select(MCACourseRegistration)
        .where(
            MCACourseRegistration.student_id == student_id,
            MCACourseRegistration.semester_number == target_semester,
            MCACourseRegistration.is_active.is_(True),
        )
        .order_by(MCACourseRegistration.id.asc())
    )
    registrations = session.execute(stmt).scalars().all()
    if not registrations:
        raise InsufficientAcademicDataError(
            f"No active course registrations found for student_id={student_id} in semester {target_semester}."
        )

    # 2. Extract course-level features and snapshot linkages
    course_features: Dict[str, Dict[str, Any]] = {}
    included_snapshots_by_course: Dict[str, Any] = {}
    missing_groups: Set[str] = set()

    attendance_pcts: List[float] = []
    mst1_scores: List[float] = []
    mst2_scores: List[float] = []
    assignment_scores: List[float] = []

    for reg in registrations:
        sc = session.get(MCASessionCourse, reg.session_course_id)
        course = session.get(MCACourse, sc.course_id) if sc else None
        course_key = course.course_code or course.course_name if course else f"reg_{reg.id}"

        att_snap = _extract_latest_attendance_snapshot(session, reg.id, cutoff)
        form_snap = _extract_latest_formative_snapshot(session, reg.id, cutoff)
        mile_snap = _extract_latest_milestone_snapshot(session, reg.id, cutoff)

        reg_snapshots: Dict[str, Optional[Dict[str, Any]]] = {}

        if att_snap is not None:
            reg_snapshots["attendance"] = {
                "snapshot_id": att_snap.id,
                "revision_number": att_snap.revision_number,
                "recorded_at": att_snap.recorded_at.isoformat() if att_snap.recorded_at else None,
            }
            if att_snap.attendance_percentage is not None:
                attendance_pcts.append(float(att_snap.attendance_percentage))
        else:
            reg_snapshots["attendance"] = None
            missing_groups.add(f"{course_key}:attendance")

        if form_snap is not None:
            reg_snapshots["formative"] = {
                "snapshot_id": form_snap.id,
                "revision_number": form_snap.revision_number,
                "recorded_at": form_snap.recorded_at.isoformat() if form_snap.recorded_at else None,
            }
            if form_snap.mst1_marks is not None:
                mst1_scores.append(float(form_snap.mst1_marks))
            if form_snap.mst2_marks is not None:
                mst2_scores.append(float(form_snap.mst2_marks))
            if form_snap.assignment_score is not None:
                assignment_scores.append(float(form_snap.assignment_score))
        else:
            reg_snapshots["formative"] = None
            missing_groups.add(f"{course_key}:formative")

        if mile_snap is not None:
            reg_snapshots["milestone"] = {
                "snapshot_id": mile_snap.id,
                "revision_number": mile_snap.revision_number,
                "recorded_at": mile_snap.recorded_at.isoformat() if mile_snap.recorded_at else None,
            }
        else:
            reg_snapshots["milestone"] = None
            if course and course.course_type == "project":
                missing_groups.add(f"{course_key}:milestone")

        included_snapshots_by_course[course_key] = {
            "registration_id": reg.id,
            "course_id": course.id if course else None,
            "course_type": course.course_type if course else None,
            "snapshots": reg_snapshots,
        }

        course_features[course_key] = {
            "registration_id": reg.id,
            "course_type": course.course_type if course else None,
            "attendance_percentage": float(att_snap.attendance_percentage) if att_snap and att_snap.attendance_percentage is not None else None,
            "mst1_marks": float(form_snap.mst1_marks) if form_snap and form_snap.mst1_marks is not None else None,
            "mst2_marks": float(form_snap.mst2_marks) if form_snap and form_snap.mst2_marks is not None else None,
            "assignment_score": float(form_snap.assignment_score) if form_snap and form_snap.assignment_score is not None else None,
            "viva_marks": float(form_snap.viva_marks) if form_snap and form_snap.viva_marks is not None else None,
            "lab_record_score": float(form_snap.lab_record_score) if form_snap and form_snap.lab_record_score is not None else None,
            "synopsis_approved": mile_snap.synopsis_approved if mile_snap else None,
            "implementation_pct": float(mile_snap.implementation_pct) if mile_snap and mile_snap.implementation_pct is not None else None,
        }

    # 3. Extract eligible prior semester results
    prior_results = _extract_eligible_prior_semester_results(session, student_id, target_semester, cutoff)
    if not prior_results and target_semester > 1:
        missing_groups.add("prior_semester_results")

    # Strict validation: At least one point-in-time academic snapshot across the semester courses must exist when require_snapshots=True.
    # Never generate a prediction using entirely invented or hardcoded features.
    has_any_snapshot = bool(
        attendance_pcts
        or mst1_scores
        or mst2_scores
        or assignment_scores
        or any(
            c_info.get("snapshots", {}).get("milestone") is not None
            for c_info in included_snapshots_by_course.values()
        )
    )
    if require_snapshots and not has_any_snapshot:
        raise InsufficientAcademicDataError(
            f"No eligible academic snapshots found across enrolled courses for student_id={student_id} "
            f"in semester {target_semester} at or before cutoff timestamp {cutoff.isoformat()}. "
            "A semester prediction cannot be generated without at least one point-in-time academic snapshot."
        )

    prior_features = _build_prior_results_features(prior_results)

    # 4. Compute semester-level aggregates
    avg_att = round(sum(attendance_pcts) / len(attendance_pcts), 2) if attendance_pcts else None
    min_att = min(attendance_pcts) if attendance_pcts else None
    avg_mst1 = round(sum(mst1_scores) / len(mst1_scores), 2) if mst1_scores else None
    avg_mst2 = round(sum(mst2_scores) / len(mst2_scores), 2) if mst2_scores else None
    avg_assign = round(sum(assignment_scores) / len(assignment_scores), 2) if assignment_scores else None

    features = {
        "total_enrolled_courses": len(registrations),
        "courses_with_attendance": len(attendance_pcts),
        "average_attendance_percentage": avg_att,
        "min_attendance_percentage": min_att,
        "courses_with_mst1": len(mst1_scores),
        "average_mst1_marks": avg_mst1,
        "courses_with_mst2": len(mst2_scores),
        "average_mst2_marks": avg_mst2,
        "courses_with_assignment": len(assignment_scores),
        "average_assignment_score": avg_assign,
        "course_features": course_features,
        **prior_features,
    }

    metadata = {
        "student_id": student.id,
        "student_code": student.student_code,
        "prediction_scope": "semester",
        "target_semester": target_semester,
        "registration_ids": [r.id for r in registrations],
        "cutoff_timestamp": cutoff.isoformat(),
        "included_snapshots_by_course": included_snapshots_by_course,
        "included_semester_results": [
            {
                "id": r.id,
                "semester_number": r.semester_number,
                "sgpa": float(r.sgpa),
                "cgpa": float(r.cgpa) if r.cgpa is not None else None,
                "declared_at": r.declared_at.isoformat() if r.declared_at else None,
                "recorded_at": r.recorded_at.isoformat() if r.recorded_at else None,
            }
            for r in prior_results
        ],
        "missing_feature_groups": sorted(missing_groups),
    }

    return {
        "metadata": metadata,
        "features": features,
    }


# ===========================================================================
# Unified Dispatcher
# ===========================================================================

def extract_academic_features(
    session: Session,
    scope: str,
    cutoff_timestamp: datetime,
    *,
    registration_id: Optional[int] = None,
    student_id: Optional[int] = None,
    target_semester: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Unified entry point for MCA academic feature extraction.

    Args:
        session: Active SQLAlchemy Session.
        scope: 'subject' or 'semester'.
        cutoff_timestamp: Point-in-time freshness boundary.
        registration_id: Required for 'subject' scope.
        student_id: Required for 'semester' scope.
        target_semester: Required for 'semester' scope (1-4).

    Returns:
        Deterministic feature payload containing 'metadata' and 'features'.
    """
    scope_normalized = (scope or "").strip().lower()

    if scope_normalized == "subject":
        if registration_id is None:
            raise InvalidPredictionScopeError(
                "registration_id is required when prediction scope is 'subject'."
            )
        return extract_subject_academic_features(
            session=session,
            registration_id=registration_id,
            cutoff_timestamp=cutoff_timestamp,
        )

    elif scope_normalized == "semester":
        if student_id is None or target_semester is None:
            raise InvalidPredictionScopeError(
                "Both student_id and target_semester are required when prediction scope is 'semester'."
            )
        return extract_semester_academic_features(
            session=session,
            student_id=student_id,
            target_semester=target_semester,
            cutoff_timestamp=cutoff_timestamp,
        )

    else:
        raise InvalidPredictionScopeError(
            f"Unsupported prediction scope: '{scope}'. Must be 'subject' or 'semester'."
        )
