"""
backend/app/routers/mca_predictions.py

FastAPI router for Master of Computer Applications (MCA) AI performance predictions.
Provides point-in-time prediction endpoints for subject-level and semester-level scopes
using trained Phase 3A ML pipelines, Phase 2E academic feature extraction, and immutable
prediction persistence.

Endpoints:
- POST /api/mca/predictions/subject: Point-in-time prediction for a course registration.
- POST /api/mca/predictions/semester: Point-in-time prediction for an entire semester roster.
- GET  /api/mca/predictions/{prediction_id}: Retrieve an immutable prediction record by ID.
- GET  /api/mca/predictions/student/{student_id}: List historical prediction records for a student.
"""

from datetime import datetime
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.exc import DatabaseError, OperationalError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import MCAPredictionRecord, MCACourse, MCASessionCourse, MCACourseRegistration
from app.schemas.mca import (
    McaPredictionApiResponse,
    McaSemesterPredictionApiRequest,
    McaSubjectPredictionApiRequest,
)
from app.services.mca_feature_extraction import (
    EntityNotFoundError,
    InsufficientAcademicDataError,
    InvalidCutoffTimestampError,
    InvalidPredictionScopeError,
)
from app.services.mca_prediction_service import (
    InvalidPredictionPayloadError,
    PredictionPersistenceError,
    get_mca_prediction_by_id,
    list_mca_predictions_by_student,
    predict_and_persist_semester_performance,
    predict_and_persist_subject_performance,
)

logger = logging.getLogger("mca_predictions_router")

router = APIRouter(prefix="/predictions", tags=["MCA Predictions"])


# ===========================================================================
# Prediction Endpoints
# ===========================================================================

@router.post(
    "/subject",
    response_model=McaPredictionApiResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict MCA subject-level performance tier",
    response_description="Point-in-time subject prediction outcome, probabilities, and persisted record ID.",
)
def predict_subject_level(
    request: McaSubjectPredictionApiRequest,
    db: Session = Depends(get_db),
) -> McaPredictionApiResponse:
    """
    Generate and persist a point-in-time performance prediction for a specific MCA course registration.

    Enforces:
    - Point-in-time temporal cutoff: snapshots recorded after cutoff are excluded (no leakage).
    - Preserves missing academic features as None (never fabricates attendance or scores).
    - Model selection: Phase 3A subject-level classification pipeline (Logistic Regression).
    - Immutable audit persistence into `mca_prediction_records`.
    - Returns mandatory synthetic-data prototype disclaimer.
    """
    try:
        result = predict_and_persist_subject_performance(
            session=db,
            registration_id=request.registration_id,
            cutoff_timestamp=request.cutoff_timestamp,
            student_id=request.student_id,
        )
        return McaPredictionApiResponse(**result)

    except EntityNotFoundError as exc:
        logger.warning(f"Entity not found in subject prediction: {exc}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    except (
        InvalidCutoffTimestampError,
        InvalidPredictionPayloadError,
        InvalidPredictionScopeError,
        InsufficientAcademicDataError,
    ) as exc:
        logger.warning(f"Validation / insufficient data in subject prediction: {exc}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    except FileNotFoundError as exc:
        logger.error(f"Trained model artifact missing: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Model artifact not available: {exc}",
        )

    except (OperationalError, DatabaseError) as exc:
        logger.error(f"Database error during subject prediction: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable. Cannot connect to database to extract academic features.",
        )

    except PredictionPersistenceError as exc:
        logger.error(f"Database persistence failure: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to persist prediction audit record: {exc}",
        )

    except Exception as exc:
        logger.error(f"Unexpected error in subject prediction: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing subject prediction.",
        )


@router.post(
    "/semester",
    response_model=McaPredictionApiResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict MCA semester-level performance tier",
    response_description="Point-in-time semester prediction outcome, probabilities, and persisted record ID.",
)
def predict_semester_level(
    request: McaSemesterPredictionApiRequest,
    db: Session = Depends(get_db),
) -> McaPredictionApiResponse:
    """
    Generate and persist a point-in-time performance prediction for an entire target semester of a student.

    Enforces:
    - Point-in-time temporal cutoff across all enrolled semester courses.
    - Excludes final examination results for the target semester (no leakage).
    - Model selection: Phase 3A semester-level classification pipeline (Random Forest).
    - Immutable audit persistence into `mca_prediction_records`.
    - Returns mandatory synthetic-data prototype disclaimer.
    """
    try:
        result = predict_and_persist_semester_performance(
            session=db,
            student_id=request.student_id,
            target_semester=request.target_semester,
            cutoff_timestamp=request.cutoff_timestamp,
        )
        return McaPredictionApiResponse(**result)

    except EntityNotFoundError as exc:
        logger.warning(f"Entity not found in semester prediction: {exc}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    except (
        InvalidCutoffTimestampError,
        InvalidPredictionPayloadError,
        InvalidPredictionScopeError,
        InsufficientAcademicDataError,
    ) as exc:
        logger.warning(f"Validation / insufficient data in semester prediction: {exc}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    except FileNotFoundError as exc:
        logger.error(f"Trained model artifact missing: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Model artifact not available: {exc}",
        )

    except (OperationalError, DatabaseError) as exc:
        logger.error(f"Database error during semester prediction: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable. Cannot connect to database to extract academic features.",
        )

    except PredictionPersistenceError as exc:
        logger.error(f"Database persistence failure: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to persist prediction audit record: {exc}",
        )

    except Exception as exc:
        logger.error(f"Unexpected error in semester prediction: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing semester prediction.",
        )


# ===========================================================================
# Retrieval Endpoints
# ===========================================================================

@router.get(
    "/{prediction_id}",
    response_model=McaPredictionApiResponse,
    summary="Get persisted MCA prediction record by ID",
    response_description="Persisted prediction record including immutable feature snapshot.",
)
def get_prediction_record(
    prediction_id: int = Path(..., gt=0, description="Unique prediction record ID"),
    db: Session = Depends(get_db),
) -> McaPredictionApiResponse:
    """Retrieve an immutable historical prediction record by its primary key."""
    try:
        record = get_mca_prediction_by_id(db, prediction_id)
    except (OperationalError, DatabaseError) as exc:
        logger.error(f"Database error in get_prediction_record: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable. Cannot connect to database to retrieve prediction record.",
        )

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCAPredictionRecord with id={prediction_id} not found.",
        )

    # Determine scope and metadata
    scope = "subject" if record.registration_id is not None else "semester"
    course = db.get(MCACourse, record.course_id) if record.course_id else None
    
    # Extract target semester from input snapshot or registration
    target_sem = 1
    if isinstance(record.input_snapshot_json, dict):
        meta = record.input_snapshot_json.get("metadata", {})
        target_sem = meta.get("target_semester", 1)

    probs = record.prediction_probabilities_json or {}
    confidence = float(max(probs.values())) if probs else 1.0

    return McaPredictionApiResponse(
        prediction_id=record.id,
        scope=scope,
        student_id=record.student_id,
        registration_id=record.registration_id,
        course_id=record.course_id,
        course_code=course.course_code if course else None,
        course_name=course.course_name if course else None,
        target_semester=target_sem,
        predicted_tier=record.predicted_tier,
        confidence=confidence,
        probabilities=probs,
        cutoff_timestamp=record.cutoff_timestamp,
        model_name=record.model_name,
        model_version=record.model_version,
        input_snapshot_json=record.input_snapshot_json,
        synthetic_data_warning=(
            "WARNING: This prediction was produced by a prototype model trained exclusively "
            "on synthetic data (Phase 3A). It must NOT be used for actual academic decisions."
        ),
        created_at=record.created_at,
    )


@router.get(
    "/student/{student_id}",
    response_model=List[McaPredictionApiResponse],
    summary="List historical prediction records for an MCA student",
    response_description="Ordered list of historical prediction audit records (newest first).",
)
def list_student_predictions(
    student_id: int = Path(..., gt=0, description="MCA Student ID"),
    limit: int = Query(50, ge=1, le=200, description="Maximum records to return"),
    db: Session = Depends(get_db),
) -> List[McaPredictionApiResponse]:
    """Retrieve all historical point-in-time predictions recorded for a specific MCA student."""
    try:
        records = list_mca_predictions_by_student(db, student_id, limit=limit)
    except (OperationalError, DatabaseError) as exc:
        logger.error(f"Database error in list_student_predictions: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable. Cannot connect to database to retrieve student predictions.",
        )
    response_items = []

    for r in records:
        scope = "subject" if r.registration_id is not None else "semester"
        course = db.get(MCACourse, r.course_id) if r.course_id else None
        target_sem = 1
        if isinstance(r.input_snapshot_json, dict):
            meta = r.input_snapshot_json.get("metadata", {})
            target_sem = meta.get("target_semester", 1)

        probs = r.prediction_probabilities_json or {}
        confidence = float(max(probs.values())) if probs else 1.0

        response_items.append(
            McaPredictionApiResponse(
                prediction_id=r.id,
                scope=scope,
                student_id=r.student_id,
                registration_id=r.registration_id,
                course_id=r.course_id,
                course_code=course.course_code if course else None,
                course_name=course.course_name if course else None,
                target_semester=target_sem,
                predicted_tier=r.predicted_tier,
                confidence=confidence,
                probabilities=probs,
                cutoff_timestamp=r.cutoff_timestamp,
                model_name=r.model_name,
                model_version=r.model_version,
                input_snapshot_json=r.input_snapshot_json,
                synthetic_data_warning=(
                    "WARNING: This prediction was produced by a prototype model trained exclusively "
                    "on synthetic data (Phase 3A). It must NOT be used for actual academic decisions."
                ),
                created_at=r.created_at,
            )
        )

    return response_items
