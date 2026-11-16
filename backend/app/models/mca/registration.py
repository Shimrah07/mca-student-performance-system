"""
backend/app/models/mca/registration.py

MCA Course Registration Model.
Adheres strictly to the Phase 2B Final Implementation Contract.
"""

from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    CheckConstraint,
    Index,
)
from sqlalchemy.orm import relationship

from app.database import Base


class MCACourseRegistration(Base):
    """
    Course enrollment per student with explicit academic attempt classification
    and soft-deactivation support.
    """
    __tablename__ = "mca_course_registrations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(
        Integer,
        ForeignKey("mca_students.id", ondelete="RESTRICT"),
        nullable=False,
        doc="Enrolled student reference (AMD-01: RESTRICT)",
    )
    session_course_id = Column(
        Integer,
        ForeignKey("mca_session_courses.id", ondelete="RESTRICT"),
        nullable=False,
        doc="Offered session course reference",
    )
    semester_number = Column(
        Integer,
        nullable=False,
        doc="Semester during which course was attempted (1 to 4)",
    )
    attempt_type = Column(
        String(20),
        nullable=False,
        default="regular",
        doc="Attempt classification: 'regular', 'backlog', 'supplementary', 'improvement'",
    )
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        doc="Soft-deactivation status flag for registration (AMD-06)",
    )
    registered_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        doc="Formal registration timestamp",
    )

    __table_args__ = (
        CheckConstraint("semester_number IN (1, 2, 3, 4)", name="ck_mca_registration_semester_number"),
        CheckConstraint(
            "attempt_type IN ('regular', 'backlog', 'supplementary', 'improvement')",
            name="ck_mca_registration_attempt_type",
        ),
        Index("ix_mca_course_reg_student_session_course", "student_id", "session_course_id"),
    )

    # Relationships
    student = relationship("MCAStudent", back_populates="registrations")
    session_course = relationship("MCASessionCourse", back_populates="registrations")
    attendance_snapshots = relationship("MCAAttendanceSnapshot", back_populates="registration", passive_deletes=True)
    formative_snapshots = relationship("MCAFormativeSnapshot", back_populates="registration", passive_deletes=True)
    milestone_snapshots = relationship("MCAProjectMilestoneSnapshot", back_populates="registration", passive_deletes=True)
    predictions = relationship("MCAPredictionRecord", back_populates="registration", passive_deletes=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "student_id": self.student_id,
            "session_course_id": self.session_course_id,
            "semester_number": self.semester_number,
            "attempt_type": self.attempt_type,
            "is_active": self.is_active,
            "registered_at": self.registered_at.isoformat() if self.registered_at else None,
        }

    def __repr__(self) -> str:
        return (
            f"<MCACourseRegistration(id={self.id}, student_id={self.student_id}, "
            f"session_course_id={self.session_course_id}, sem={self.semester_number}, "
            f"attempt='{self.attempt_type}', active={self.is_active})>"
        )
