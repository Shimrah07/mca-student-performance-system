"""
backend/app/models/mca/prediction.py

MCA AI Prediction Record Model.
Adheres strictly to the Phase 2B Final Implementation Contract.
"""

from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    JSON,
    Index,
)
from sqlalchemy.orm import relationship

from app.database import Base


class MCAPredictionRecord(Base):
    """
    Immutable audit record of MCA AI inference events, probabilities,
    input feature snapshots, and recommendations.
    Preserves cutoff_timestamp separately from database creation timestamp (created_at).
    """
    __tablename__ = "mca_prediction_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(
        Integer,
        ForeignKey("mca_students.id", ondelete="SET NULL"),
        nullable=True,
        doc="Optional student reference; SET NULL on student deletion (AMD-10)",
    )
    registration_id = Column(
        Integer,
        ForeignKey("mca_course_registrations.id", ondelete="SET NULL"),
        nullable=True,
        doc="Optional registration reference; SET NULL on registration deletion (AMD-10)",
    )
    course_id = Column(
        Integer,
        ForeignKey("mca_courses.id", ondelete="RESTRICT"),
        nullable=True,
        doc="Course context; nullable for semester-level predictions (RESTRICT)",
    )
    predicted_tier = Column(
        String(50),
        nullable=False,
        doc="Predicted category: 'Excellent', 'Good', 'Average', 'Needs Improvement'",
    )
    model_name = Column(
        String(100),
        nullable=False,
        doc="Classifier identifier (e.g. 'mca_scenario_a_gradient_boost')",
    )
    model_version = Column(
        String(50),
        nullable=False,
        default="1.0.0",
        doc="Model semantic training release identifier",
    )
    input_snapshot_json = Column(
        JSON,
        nullable=False,
        doc="Immutable snapshot of all input features used at inference",
    )
    prediction_probabilities_json = Column(
        JSON,
        nullable=True,
        doc="Indicative class probability distribution",
    )
    cutoff_timestamp = Column(
        DateTime,
        nullable=False,
        doc="Exact academic-data freshness boundary for evaluated features",
    )
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        doc="Database persistence timestamp",
    )

    __table_args__ = (
        Index("ix_mca_prediction_records_cutoff_student", "cutoff_timestamp", "student_id"),
    )

    # Relationships
    student = relationship("MCAStudent", back_populates="predictions")
    registration = relationship("MCACourseRegistration", back_populates="predictions")
    course = relationship("MCACourse", back_populates="predictions")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "student_id": self.student_id,
            "registration_id": self.registration_id,
            "course_id": self.course_id,
            "predicted_tier": self.predicted_tier,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "input_snapshot_json": self.input_snapshot_json,
            "prediction_probabilities_json": self.prediction_probabilities_json,
            "cutoff_timestamp": self.cutoff_timestamp.isoformat() if self.cutoff_timestamp else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return (
            f"<MCAPredictionRecord(id={self.id}, student_id={self.student_id}, "
            f"tier='{self.predicted_tier}', model='{self.model_name}', "
            f"cutoff='{self.cutoff_timestamp}')>"
        )
