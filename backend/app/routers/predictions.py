"""
backend/app/routers/predictions.py

FastAPI router for student performance prediction and historical record retrieval.

Endpoints:
- POST /api/predictions: Validates student features, invokes ML candidate pipeline,
  generates rule-based recommendations, and safely persists history if database is reachable.
- GET  /api/predictions/{prediction_id}: Retrieves a previously persisted prediction record.
- GET  /api/predictions: Returns a paginated list of recent prediction records.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_db
from app.models.student import Student
from app.models.prediction import PredictionRecord
from app.schemas.prediction import (
    PredictionRequest,
    PredictionResponse,
    PredictionHistoryItem,
    PredictionListResponse,
)
from app.services.prediction_service import predict_and_recommend

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/predictions", tags=["Predictions"])


@router.post(
    "",
    response_model=PredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict student performance category and generate recommendations",
)
def predict_student_performance(
    request: PredictionRequest,
    db: Session = Depends(get_db),
):
    """
    Predict a student's academic performance tier (Excellent, Good, Average, Needs Improvement)
    and generate supportive, rule-based academic guidance.

    Features:
    - Rejects target-leaking attributes (G2, G3).
    - Excludes G1 in Scenario A; enforces G1 in Scenario B.
    - Yields uncalibrated indicative probability estimates.
    - Preserves historical records when the database is available.
    - Operates smoothly without crashing if database is offline.
    """
    # 1. Execute ML pipeline inference and recommendation generation
    try:
        features_dict = request.features.model_dump()
        result = predict_and_recommend(
            subject=request.subject.value,
            scenario=request.scenario.value,
            features_dict=features_dict,
        )
    except FileNotFoundError as exc:
        logger.error("Model artifact not found: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    except ValueError as exc:
        logger.warning("Invalid input to prediction service: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error("Inference execution failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during prediction inference.",
        )

    # 2. Attempt safe database persistence
    persisted = False
    prediction_id: Optional[int] = None
    created_at_val = None

    try:
        student_id_val = None

        # Link to student if an anonymized student_code was provided
        if request.student_code:
            code = request.student_code.strip()
            student = db.query(Student).filter(Student.student_code == code).first()
            if not student:
                student = Student(student_code=code)
                db.add(student)
                db.flush()
            student_id_val = student.id

        # Package composite recommendations payload
        recs_composite = {
            "summary": result["summary"],
            "actionable_recommendations": result["actionable_recommendations"],
            "strengths_identified": result["strengths_identified"],
            "evaluated_factors": result["evaluated_factors"],
            "disclaimer": result["disclaimer"],
        }

        # Create immutable prediction record
        record = PredictionRecord(
            student_id=student_id_val,
            subject=result["subject"],
            scenario=result["scenario"],
            model_name=result["model_name"],
            model_version=result["model_version"],
            predicted_category=result["predicted_category"],
            prediction_probabilities=result["prediction_probabilities"],
            input_features=result["clean_input_snapshot"],
            weak_areas=result["weak_areas"],
            recommendations=recs_composite,
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        persisted = True
        prediction_id = record.id
        created_at_val = record.created_at
    except (SQLAlchemyError, Exception) as exc:
        # Graceful fallback: log and return unpersisted prediction without failing request
        try:
            db.rollback()
        except Exception:
            pass
        logger.warning("Database persistence skipped or failed: %s", exc)
        persisted = False
        prediction_id = None

    return PredictionResponse(
        predicted_category=result["predicted_category"],
        subject=result["subject"],
        scenario=result["scenario"],
        model_name=result["model_name"],
        model_version=result["model_version"],
        prediction_probabilities=result["prediction_probabilities"],
        summary=result["summary"],
        actionable_recommendations=result["actionable_recommendations"],
        strengths_identified=result["strengths_identified"],
        evaluated_factors=result["evaluated_factors"],
        disclaimer=result["disclaimer"],
        prediction_id=prediction_id,
        persisted=persisted,
        created_at=created_at_val,
    )


@router.get(
    "/{prediction_id}",
    response_model=PredictionHistoryItem,
    summary="Retrieve a saved prediction record by ID",
)
def get_prediction_by_id(
    prediction_id: int,
    db: Session = Depends(get_db),
):
    """
    Retrieve details of a previously persisted prediction record.
    """
    try:
        record = db.query(PredictionRecord).filter(PredictionRecord.id == prediction_id).first()
    except SQLAlchemyError as exc:
        logger.error("Database query failed for prediction_id=%s: %s", prediction_id, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable.",
        )

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prediction record with ID {prediction_id} not found.",
        )

    return PredictionHistoryItem(
        id=record.id,
        student_id=record.student_id,
        subject=record.subject,
        scenario=record.scenario,
        model_name=record.model_name,
        model_version=record.model_version,
        predicted_category=record.predicted_category,
        prediction_probabilities=record.prediction_probabilities,
        input_features=record.input_features,
        weak_areas=record.weak_areas,
        recommendations=record.recommendations,
        created_at=record.created_at.isoformat() if record.created_at else None,
    )


@router.get(
    "",
    response_model=PredictionListResponse,
    summary="List recent prediction records with pagination",
)
def list_predictions(
    limit: int = Query(10, ge=1, le=100, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db),
):
    """
    Return a paginated list of recent prediction records ordered by creation date descending.
    """
    try:
        total = db.query(PredictionRecord).count()
        records = (
            db.query(PredictionRecord)
            .order_by(PredictionRecord.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
    except SQLAlchemyError as exc:
        logger.warning("Database unavailable for listing predictions: %s", exc)
        return PredictionListResponse(total=0, items=[])

    items = [
        PredictionHistoryItem(
            id=r.id,
            student_id=r.student_id,
            subject=r.subject,
            scenario=r.scenario,
            model_name=r.model_name,
            model_version=r.model_version,
            predicted_category=r.predicted_category,
            prediction_probabilities=r.prediction_probabilities,
            input_features=r.input_features,
            weak_areas=r.weak_areas,
            recommendations=r.recommendations,
            created_at=r.created_at.isoformat() if r.created_at else None,
        )
        for r in records
    ]

    return PredictionListResponse(total=total, items=items)
