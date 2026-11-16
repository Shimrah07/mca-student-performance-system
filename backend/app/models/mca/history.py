"""
backend/app/models/mca/history.py

MCA Historical Semester Results Model.
Adheres strictly to the Phase 2B Final Implementation Contract.
"""

from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy import (
    Column,
    Integer,
    DateTime,
    Numeric,
    ForeignKey,
    CheckConstraint,
    Index,
)
from sqlalchemy.orm import relationship

from app.database import Base


class MCASemesterResult(Base):
    """
    Immutable historical record of finalized semester examination performance.
    Preserves both official university declaration timestamp (declared_at)
    and database insertion timestamp (recorded_at).
    """
    __tablename__ = "mca_semester_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(
        Integer,
        ForeignKey("mca_students.id", ondelete="RESTRICT"),
        nullable=False,
        doc="Evaluated student reference (AMD-02: RESTRICT)",
    )
    session_id = Column(
        Integer,
        ForeignKey("mca_academic_sessions.id", ondelete="RESTRICT"),
        nullable=False,
        doc="Cohort academic session reference",
    )
    semester_number = Column(
        Integer,
        nullable=False,
        doc="Completed semester number (1 to 4)",
    )
    sgpa = Column(
        Numeric(4, 2),
        nullable=False,
        doc="Semester Grade Point Average (0.00 to 10.00)",
    )
    cgpa = Column(
        Numeric(4, 2),
        nullable=True,
        doc="Official Cumulative GPA at time of declaration (0.00 to 10.00)",
    )
    declared_at = Column(
        DateTime,
        nullable=True,
        doc="Official university gazette publication timestamp; NULL if pending",
    )
    recorded_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        doc="Database write timestamp",
    )

    __table_args__ = (
        CheckConstraint("semester_number IN (1, 2, 3, 4)", name="ck_mca_result_semester_number"),
        CheckConstraint("sgpa >= 0.00 AND sgpa <= 10.00", name="ck_mca_result_sgpa_range"),
        CheckConstraint("cgpa IS NULL OR (cgpa >= 0.00 AND cgpa <= 10.00)", name="ck_mca_result_cgpa_range"),
        Index("ix_mca_semester_results_student_semester", "student_id", "semester_number"),
    )

    # Relationships
    student = relationship("MCAStudent", back_populates="semester_results")
    session = relationship("MCAAcademicSession", back_populates="semester_results")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "student_id": self.student_id,
            "session_id": self.session_id,
            "semester_number": self.semester_number,
            "sgpa": float(self.sgpa) if self.sgpa is not None else None,
            "cgpa": float(self.cgpa) if self.cgpa is not None else None,
            "declared_at": self.declared_at.isoformat() if self.declared_at else None,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
        }

    def __repr__(self) -> str:
        return (
            f"<MCASemesterResult(id={self.id}, student_id={self.student_id}, "
            f"sem={self.semester_number}, sgpa={self.sgpa}, cgpa={self.cgpa})>"
        )
