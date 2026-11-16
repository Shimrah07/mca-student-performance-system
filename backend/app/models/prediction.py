"""
backend/app/models/prediction.py

PredictionRecord ORM model.

Stores an academic performance prediction event and its associated supportive guidance.

Key Design Decisions:
- Supports the workflow:
    1. Receive student input features.
    2. Predict performance category (Excellent / Good / Average / Needs Improvement).
    3. Generate supportive rule-based recommendations.
    4. Preserve historical records for faculty/student review.
- Encapsulates input features as a JSON dictionary snapshot, supporting both Scenario A
  (30 features) and Scenario B (31 features with G1) without rigid column constraints.
- Stores model metadata (model_name, model_version) for auditability and experiment tracking.
- Stores probability estimates (as JSON) labelled strictly as indicative model estimates,
  not guaranteed real-world risk.
- Stores structured recommendation outputs (as JSON) from ml/src/recommendations.py.
- Links optionally to Student via student_id foreign key (nullable=True enables anonymous
  quick predictions or bulk evaluations).
"""

from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.database import Base


class PredictionRecord(Base):
    """
    Represents an immutable record of an academic prediction and its recommendations.
    """
    __tablename__ = "prediction_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(
        Integer,
        ForeignKey("students.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Optional link to student entity; nullable to support anonymous/guest predictions",
    )
    subject = Column(
        String(20),
        nullable=False,
        index=True,
        doc="Subject evaluated ('Mathematics' or 'Portuguese')",
    )
    scenario = Column(
        String(20),
        nullable=False,
        index=True,
        doc="Prediction scenario ('Scenario A' [Early-Warning] or 'Scenario B' [Mid-Term])",
    )
    model_name = Column(
        String(100),
        nullable=False,
        doc="Classifier used (e.g. 'student_mat_scenario_a_logistic_regression')",
    )
    model_version = Column(
        String(50),
        nullable=False,
        default="1.0.0",
        doc="Semantic model version or training run identifier",
    )
    predicted_category = Column(
        String(50),
        nullable=False,
        index=True,
        doc="Predicted category: 'Excellent', 'Good', 'Average', 'Needs Improvement'",
    )
    prediction_probabilities = Column(
        JSON,
        nullable=True,
        doc="Estimated class probabilities dictionary (e.g. {'Average': 0.60, ...})",
    )
    input_features = Column(
        JSON,
        nullable=False,
        doc="Snapshot of features submitted at prediction time (strictly excludes G2 and G3)",
    )
    weak_areas = Column(
        JSON,
        nullable=True,
        doc="Identified academic risk factors/indicators (e.g. ['studytime', 'absences'])",
    )
    recommendations = Column(
        JSON,
        nullable=True,
        doc="Supportive rule-based recommendations payload from ml/src/recommendations.py",
    )
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
        doc="Timestamp when prediction was generated",
    )

    # Relationships
    student = relationship("Student", back_populates="predictions")

    def to_dict(self) -> Dict[str, Any]:
        """Convert prediction record to dictionary representation."""
        return {
            "id": self.id,
            "student_id": self.student_id,
            "subject": self.subject,
            "scenario": self.scenario,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "predicted_category": self.predicted_category,
            "prediction_probabilities": self.prediction_probabilities,
            "input_features": self.input_features,
            "weak_areas": self.weak_areas,
            "recommendations": self.recommendations,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return (
            f"<PredictionRecord(id={self.id}, subject='{self.subject}', "
            f"scenario='{self.scenario}', category='{self.predicted_category}')>"
        )
