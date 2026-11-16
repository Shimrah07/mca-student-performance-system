"""
backend/app/models/mca/assessment.py

MCA Assessment Events Model.
Adheres strictly to the Phase 2B Final Implementation Contract.
"""

from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    DateTime,
    Numeric,
    ForeignKey,
    CheckConstraint,
    event,
)
from sqlalchemy.orm import relationship, validates

from app.database import Base


class MCAAssessmentEvent(Base):
    """
    Master schedule and definitions of formative/summative tests and makeup events.
    Contains no per-student data; acts as an event catalog per session-course.
    """
    __tablename__ = "mca_assessment_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_course_id = Column(
        Integer,
        ForeignKey("mca_session_courses.id", ondelete="RESTRICT"),
        nullable=False,
        doc="Offered session course reference",
    )
    event_name = Column(
        String(100),
        nullable=False,
        doc="Event title: e.g. 'Mid Semester Test 1', 'Assignment 1'",
    )
    event_type = Column(
        String(50),
        nullable=False,
        doc="Event archetype: e.g. 'MST', 'ASSIGNMENT', 'VIVA', 'MAKEUP'",
    )
    max_marks = Column(
        Numeric(5, 2),
        nullable=False,
        doc="Maximum points achievable (e.g. 20.00)",
    )
    event_date = Column(
        Date,
        nullable=True,
        doc="Scheduled or administered calendar date",
    )
    original_event_id = Column(
        Integer,
        ForeignKey("mca_assessment_events.id", ondelete="RESTRICT"),
        nullable=True,
        doc="Self-reference for makeup events. NULL for originals; references original for makeups (FK-11)",
    )
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        doc="Record creation timestamp",
    )

    __table_args__ = (
        CheckConstraint("max_marks > 0", name="ck_mca_assessment_event_max_marks"),
        CheckConstraint(
            "original_event_id IS NULL OR original_event_id != id",
            name="ck_mca_assessment_event_no_self_ref",
        ),
    )

    # Relationships
    session_course = relationship("MCASessionCourse", back_populates="assessment_events")

    # Self-referencing relationship for makeup events
    original_event = relationship(
        "MCAAssessmentEvent",
        remote_side=[id],
        back_populates="makeup_events",
        foreign_keys=[original_event_id],
        passive_deletes=True,
    )
    makeup_events = relationship(
        "MCAAssessmentEvent",
        back_populates="original_event",
        foreign_keys=[original_event_id],
        passive_deletes=True,
    )

    @validates("original_event_id")
    def validate_original_event_id(self, key: str, value: int | None) -> int | None:
        """
        Application-level validation to prevent self-referencing makeup events.
        Replicates ck_mca_assessment_event_no_self_ref at the ORM layer.
        """
        if value is not None and self.id is not None and value == self.id:
            raise ValueError(
                f"ck_mca_assessment_event_no_self_ref violation: "
                f"original_event_id ({value}) cannot equal assessment event id ({self.id})."
            )
        return value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_course_id": self.session_course_id,
            "event_name": self.event_name,
            "event_type": self.event_type,
            "max_marks": float(self.max_marks) if self.max_marks is not None else None,
            "event_date": self.event_date.isoformat() if self.event_date else None,
            "original_event_id": self.original_event_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return (
            f"<MCAAssessmentEvent(id={self.id}, name='{self.event_name}', "
            f"type='{self.event_type}', session_course_id={self.session_course_id}, "
            f"original_event_id={self.original_event_id})>"
        )


@event.listens_for(MCAAssessmentEvent, "before_insert")
@event.listens_for(MCAAssessmentEvent, "before_update")
def _validate_assessment_event_no_self_ref(mapper, connection, target: MCAAssessmentEvent):
    """
    Hook to ensure self-referencing cannot occur upon insert or update.
    """
    if target.original_event_id is not None and target.id is not None:
        if target.original_event_id == target.id:
            raise ValueError(
                f"ck_mca_assessment_event_no_self_ref violation: "
                f"original_event_id ({target.original_event_id}) cannot equal assessment event id ({target.id})."
            )
