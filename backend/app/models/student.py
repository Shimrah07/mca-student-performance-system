"""
backend/app/models/student.py

Student ORM model.

Design & Privacy:
- Follows the approved Week III SRS and Week IV System Design.
- Represents a student using an anonymized, non-sensitive identifier (student_code).
- Strictly preserves student privacy: NEVER stores student names, emails, phone numbers,
  or other directly identifying personal data.
- Relates 1-to-N with PredictionRecord.
"""

from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship

from app.database import Base


class Student(Base):
    """
    Represents an enrolled student using an anonymized reference code.
    """
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_code = Column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
        doc="Anonymized student identifier (e.g. 'STU-001', 'ANON-1042')",
    )
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc="Timestamp when student record was created",
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc="Timestamp when student record was last updated",
    )

    # 1-to-N relationship with PredictionRecord
    predictions = relationship(
        "PredictionRecord",
        back_populates="student",
        cascade="all, delete-orphan",
        order_by="desc(PredictionRecord.created_at)",
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert student record to dictionary representation."""
        return {
            "id": self.id,
            "student_code": self.student_code,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<Student(id={self.id}, student_code='{self.student_code}')>"
