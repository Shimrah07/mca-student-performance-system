"""
backend/app/models/mca/student.py

MCA Student Entity Model.
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
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship

from app.database import Base


class MCAStudent(Base):
    """
    Represents an enrolled MCA student using an anonymized reference code,
    permanently anchored to an intake cohort academic session.
    """
    __tablename__ = "mca_students"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_code = Column(
        String(50),
        nullable=False,
        doc="Anonymized student identifier (e.g. 'MCA-2026-001')",
    )
    session_id = Column(
        Integer,
        ForeignKey("mca_academic_sessions.id", ondelete="RESTRICT"),
        nullable=False,
        doc="Intake cohort academic session reference",
    )
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        doc="Soft-deactivation status flag (AMD-03)",
    )
    deactivated_at = Column(
        DateTime,
        nullable=True,
        doc="Timestamp when student was deactivated (AMD-04)",
    )
    deactivation_reason = Column(
        String(255),
        nullable=True,
        doc="Administrative justification for deactivation (AMD-05)",
    )
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        doc="Record creation timestamp",
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        doc="Record last update timestamp",
    )

    __table_args__ = (
        UniqueConstraint("student_code", name="uq_mca_student_code"),
        Index("ix_mca_students_student_code", "student_code"),
    )

    # Relationships
    session = relationship("MCAAcademicSession", back_populates="students")
    registrations = relationship("MCACourseRegistration", back_populates="student", passive_deletes=True)
    semester_results = relationship("MCASemesterResult", back_populates="student", passive_deletes=True)
    predictions = relationship("MCAPredictionRecord", back_populates="student", passive_deletes=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "student_code": self.student_code,
            "session_id": self.session_id,
            "is_active": self.is_active,
            "deactivated_at": self.deactivated_at.isoformat() if self.deactivated_at else None,
            "deactivation_reason": self.deactivation_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<MCAStudent(id={self.id}, code='{self.student_code}', session_id={self.session_id}, active={self.is_active})>"
