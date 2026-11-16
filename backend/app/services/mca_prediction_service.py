"""
backend/app/services/mca_prediction_service.py

MCA AI Prediction Persistence Service.
Provides an immutable audit repository for AI inference events using
the approved MCAPredictionRecord (mca_prediction_records) schema.

Adheres strictly to Phase2B_Final_Implementation_Contract.md:
- Uses exact existing ORM columns without inventing or modifying schema fields.
- Respects nullable student_id, registration_id, and course_id relationships.
- Preserves subject-level vs. semester-level scope distinction.
- Records exact point-in-time cutoff_timestamp alongside created_at timestamp.
- Strictly append-only: every prediction creates a new row; existing records are never modified.
- Full transaction rollback on database failure.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    MCACourse,
    MCACourseRegistration,
    MCAPredictionRecord,
    MCASessionCourse,
    MCAStudent,
)
from app.services.mca_feature_extraction import (
    EntityNotFoundError,
    InvalidCutoffTimestampError,
    InvalidPredictionScopeError,
    extract_semester_academic_features,
    extract_subject_academic_features,
)
from ml.src.mca_predictor import (
    predict_semester_performance,
    predict_subject_performance,
)

logger = logging.getLogger("mca_prediction_service")

VALID_PREDICTED_TIERS = {
    "Excellent",
    "Good",
    "Average",
    "Needs Improvement",
}


# ===========================================================================
# Exceptions
# ===========================================================================

class PredictionPersistenceError(Exception):
    """Base exception for prediction persistence failures."""
    pass


class InvalidPredictionPayloadError(PredictionPersistenceError):
    """Raised when prediction input parameters violate constraints or nullability rules."""
    pass


# ===========================================================================
# Prediction Persistence Functions
# ===========================================================================

def persist_mca_prediction(
    session: Session,
    predicted_tier: str,
    model_name: str,
    cutoff_timestamp: datetime,
    input_snapshot_json: Dict[str, Any],
    *,
    model_version: str = "1.0.0",
    prediction_probabilities_json: Optional[Dict[str, float]] = None,
    student_id: Optional[int] = None,
    registration_id: Optional[int] = None,
    course_id: Optional[int] = None,
    commit: bool = True,
) -> MCAPredictionRecord:
    """
    Persist an immutable prediction event into the mca_prediction_records table.

    Args:
        session: Active SQLAlchemy Session.
        predicted_tier: Predicted performance classification.
                        Must be in {'Excellent', 'Good', 'Average', 'Needs Improvement'}.
        model_name: Classifier model identifier (e.g. 'mca_subject_scenario_a_rf').
        cutoff_timestamp: Point-in-time freshness boundary of academic data evaluated.
        input_snapshot_json: Deterministic snapshot of extracted features and metadata.
        model_version: Semantic release version of the trained model (default: '1.0.0').
        prediction_probabilities_json: Optional class probability estimates dictionary.
        student_id: Optional parent student reference. Nullable.
        registration_id: Optional parent course registration reference (subject-level). Nullable.
        course_id: Optional course reference (subject-level). Nullable for semester-level predictions.
        commit: If True, commits the transaction. If False, flushes without committing.

    Returns:
        The newly persisted MCAPredictionRecord instance.

    Raises:
        InvalidPredictionPayloadError: If required fields or validation rules fail.
        PredictionPersistenceError: If database persistence or transaction fails.
    """
    # 1. Validate required fields
    if not predicted_tier or not isinstance(predicted_tier, str):
        raise InvalidPredictionPayloadError(
            f"predicted_tier is required and must be a string, got {predicted_tier!r}."
        )
    if predicted_tier not in VALID_PREDICTED_TIERS:
        raise InvalidPredictionPayloadError(
            f"Invalid predicted_tier: {predicted_tier!r}. "
            f"Allowed values are: {sorted(VALID_PREDICTED_TIERS)}."
        )

    if not model_name or not isinstance(model_name, str) or not model_name.strip():
        raise InvalidPredictionPayloadError("model_name is required and must be a non-empty string.")

    if not model_version or not isinstance(model_version, str) or not model_version.strip():
        raise InvalidPredictionPayloadError("model_version must be a non-empty string.")

    if cutoff_timestamp is None or not isinstance(cutoff_timestamp, datetime):
        raise InvalidPredictionPayloadError(
            f"cutoff_timestamp must be an explicit datetime instance, got {cutoff_timestamp!r}."
        )

    if not isinstance(input_snapshot_json, dict) or not input_snapshot_json:
        raise InvalidPredictionPayloadError(
            "input_snapshot_json is required and must be a non-empty dictionary."
        )

    if prediction_probabilities_json is not None:
        if not isinstance(prediction_probabilities_json, dict):
            raise InvalidPredictionPayloadError(
                "prediction_probabilities_json, if provided, must be a dictionary."
            )

    # 2. Normalize cutoff timestamp (ensure UTC consistency with database)
    normalized_cutoff = cutoff_timestamp
    if cutoff_timestamp.tzinfo is not None:
        normalized_cutoff = cutoff_timestamp.astimezone(timezone.utc).replace(tzinfo=None)

    # 3. Verify foreign key existence if IDs are supplied
    if student_id is not None:
        student = session.get(MCAStudent, student_id)
        if student is None:
            raise InvalidPredictionPayloadError(f"Referenced student_id={student_id} does not exist.")

    if registration_id is not None:
        reg = session.get(MCACourseRegistration, registration_id)
        if reg is None:
            raise InvalidPredictionPayloadError(f"Referenced registration_id={registration_id} does not exist.")

    if course_id is not None:
        course = session.get(MCACourse, course_id)
        if course is None:
            raise InvalidPredictionPayloadError(f"Referenced course_id={course_id} does not exist.")

    # 4. Construct prediction record
    prediction = MCAPredictionRecord(
        student_id=student_id,
        registration_id=registration_id,
        course_id=course_id,
        predicted_tier=predicted_tier,
        model_name=model_name.strip(),
        model_version=model_version.strip(),
        input_snapshot_json=input_snapshot_json,
        prediction_probabilities_json=prediction_probabilities_json,
        cutoff_timestamp=normalized_cutoff,
    )

    # 5. Persist to database with safe rollback on failure
    try:
        session.add(prediction)
        if commit:
            session.commit()
            session.refresh(prediction)
        else:
            session.flush()
        logger.info(
            f"Persisted MCAPredictionRecord id={prediction.id} tier='{predicted_tier}' "
            f"model='{model_name}' cutoff='{normalized_cutoff}'"
        )
        return prediction

    except Exception as exc:
        session.rollback()
        logger.error(f"Failed to persist prediction record: {exc}", exc_info=True)
        raise PredictionPersistenceError(f"Transaction failed during prediction persistence: {exc}") from exc


# ===========================================================================
# Prediction Retrieval Helpers
# ===========================================================================

def get_mca_prediction_by_id(session: Session, prediction_id: int) -> Optional[MCAPredictionRecord]:
    """Retrieve an immutable prediction record by primary key."""
    return session.get(MCAPredictionRecord, prediction_id)


def list_mca_predictions_by_student(
    session: Session,
    student_id: int,
    limit: int = 100,
) -> List[MCAPredictionRecord]:
    """
    List historical prediction records for a student, ordered newest first.
    Strictly read-only.
    """
    stmt = (
        select(MCAPredictionRecord)
        .where(MCAPredictionRecord.student_id == student_id)
        .order_by(MCAPredictionRecord.created_at.desc(), MCAPredictionRecord.id.desc())
        .limit(limit)
    )
    return session.execute(stmt).scalars().all()


def list_mca_predictions_by_registration(
    session: Session,
    registration_id: int,
    limit: int = 100,
) -> List[MCAPredictionRecord]:
    """
    List historical prediction records for a specific course registration.
    Strictly read-only.
    """
    stmt = (
        select(MCAPredictionRecord)
        .where(MCAPredictionRecord.registration_id == registration_id)
        .order_by(MCAPredictionRecord.created_at.desc(), MCAPredictionRecord.id.desc())
        .limit(limit)
    )
    return session.execute(stmt).scalars().all()


# ===========================================================================
# End-to-End Prediction Orchestration (Phase 3B)
# ===========================================================================

def predict_and_persist_subject_performance(
    session: Session,
    registration_id: int,
    cutoff_timestamp: datetime,
    student_id: Optional[int] = None,
    artifacts_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute end-to-end subject-level point-in-time prediction and persistence:
    1. Validate registration entity and optional student ownership.
    2. Extract point-in-time features strictly at or before cutoff_timestamp.
    3. Generate prediction using trained Phase 3A subject pipeline.
    4. Persist immutable MCAPredictionRecord.
    5. Return unified response payload with probabilities and synthetic disclaimer.
    """
    reg = session.get(MCACourseRegistration, registration_id)
    if reg is None:
        raise EntityNotFoundError(f"MCACourseRegistration with id={registration_id} not found.")

    if student_id is not None and reg.student_id != student_id:
        raise InvalidPredictionPayloadError(
            f"Registration id={registration_id} belongs to student_id={reg.student_id}, "
            f"not requested student_id={student_id}."
        )

    # Extract point-in-time academic features via Phase 2E service
    extraction_payload = extract_subject_academic_features(
        session=session,
        registration_id=registration_id,
        cutoff_timestamp=cutoff_timestamp,
        require_snapshots=True,
    )

    # Model inference via Phase 3A predictor
    pred_res = predict_subject_performance(
        features_payload=extraction_payload,
        artifacts_dir=artifacts_dir,
    )

    # Resolve course metadata
    session_course = session.get(MCASessionCourse, reg.session_course_id) if reg.session_course_id else None
    course_id = session_course.course_id if session_course else None
    course = session.get(MCACourse, course_id) if course_id else None

    # Determine model naming
    raw_alg = pred_res["model_metadata"].get("algorithm", "logistic_regression")
    model_name = f"mca_subject_{raw_alg.lower().replace(' ', '_')}"

    # Persist immutable prediction
    record = persist_mca_prediction(
        session=session,
        predicted_tier=pred_res["predicted_tier"],
        model_name=model_name,
        cutoff_timestamp=cutoff_timestamp,
        input_snapshot_json=extraction_payload,
        model_version="1.0.0",
        prediction_probabilities_json=pred_res.get("probabilities"),
        student_id=reg.student_id,
        registration_id=reg.id,
        course_id=course_id,
        commit=True,
    )

    return {
        "prediction_id": record.id,
        "scope": "subject",
        "student_id": record.student_id,
        "registration_id": record.registration_id,
        "course_id": record.course_id,
        "course_code": course.course_code if course else None,
        "course_name": course.course_name if course else None,
        "target_semester": reg.semester_number,
        "predicted_tier": record.predicted_tier,
        "confidence": pred_res["confidence"],
        "probabilities": pred_res["probabilities"],
        "cutoff_timestamp": record.cutoff_timestamp,
        "model_name": record.model_name,
        "model_version": record.model_version,
        "input_snapshot_json": record.input_snapshot_json,
        "synthetic_data_warning": pred_res["synthetic_data_warning"],
        "created_at": record.created_at,
    }


def predict_and_persist_semester_performance(
    session: Session,
    student_id: int,
    target_semester: int,
    cutoff_timestamp: datetime,
    artifacts_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute end-to-end semester-level point-in-time prediction and persistence:
    1. Validate student entity and semester bounds.
    2. Extract point-in-time features strictly at or before cutoff_timestamp.
    3. Generate prediction using trained Phase 3A semester pipeline.
    4. Persist immutable MCAPredictionRecord (registration_id=None, course_id=None).
    5. Return unified response payload with probabilities and synthetic disclaimer.
    """
    student = session.get(MCAStudent, student_id)
    if student is None:
        raise EntityNotFoundError(f"MCAStudent with id={student_id} not found.")

    if target_semester not in (1, 2, 3, 4):
        raise InvalidPredictionScopeError(
            f"target_semester must be an integer between 1 and 4, got {target_semester}."
        )

    # Extract point-in-time academic features via Phase 2E service
    extraction_payload = extract_semester_academic_features(
        session=session,
        student_id=student_id,
        target_semester=target_semester,
        cutoff_timestamp=cutoff_timestamp,
        require_snapshots=True,
    )

    # Model inference via Phase 3A predictor
    pred_res = predict_semester_performance(
        features_payload=extraction_payload,
        artifacts_dir=artifacts_dir,
    )

    # Determine model naming
    raw_alg = pred_res["model_metadata"].get("algorithm", "random_forest")
    model_name = f"mca_semester_{raw_alg.lower().replace(' ', '_')}"

    # Persist immutable prediction
    record = persist_mca_prediction(
        session=session,
        predicted_tier=pred_res["predicted_tier"],
        model_name=model_name,
        cutoff_timestamp=cutoff_timestamp,
        input_snapshot_json=extraction_payload,
        model_version="1.0.0",
        prediction_probabilities_json=pred_res.get("probabilities"),
        student_id=student_id,
        registration_id=None,
        course_id=None,
        commit=True,
    )

    return {
        "prediction_id": record.id,
        "scope": "semester",
        "student_id": record.student_id,
        "registration_id": None,
        "course_id": None,
        "course_code": None,
        "course_name": None,
        "target_semester": target_semester,
        "predicted_tier": record.predicted_tier,
        "confidence": pred_res["confidence"],
        "probabilities": pred_res["probabilities"],
        "cutoff_timestamp": record.cutoff_timestamp,
        "model_name": record.model_name,
        "model_version": record.model_version,
        "input_snapshot_json": record.input_snapshot_json,
        "synthetic_data_warning": pred_res["synthetic_data_warning"],
        "created_at": record.created_at,
    }

