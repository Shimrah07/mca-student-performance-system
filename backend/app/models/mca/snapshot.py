"""
backend/app/models/mca/snapshot.py

MCA Point-in-Time Snapshot Models:
- MCAAttendanceSnapshot (mca_attendance_snapshots)
- MCAFormativeSnapshot (mca_formative_snapshots)
- MCAProjectMilestoneSnapshot (mca_project_milestone_snapshots)

Adheres strictly to the Phase 2B Final Implementation Contract.
"""

from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy import (
    Column,
    Integer,
    Boolean,
    DateTime,
    Numeric,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base


class MCAAttendanceSnapshot(Base):
    """
    Point-in-time sequential snapshot of attendance metrics for a course registration.
    """
    __tablename__ = "mca_attendance_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    registration_id = Column(
        Integer,
        ForeignKey("mca_course_registrations.id", ondelete="RESTRICT"),
        nullable=False,
        doc="Parent course registration reference",
    )
    revision_number = Column(
        Integer,
        nullable=False,
        doc="Monotonically increasing revision sequence (AMD-07)",
    )
    recorded_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        doc="Physical timestamp when snapshot was captured",
    )
    attendance_percentage = Column(
        Numeric(5, 2),
        nullable=True,
        doc="Percentage attendance (0.00 to 100.00)",
    )
    classes_held = Column(
        Integer,
        nullable=True,
        doc="Cumulative lectures/labs held to date",
    )
    classes_attended = Column(
        Integer,
        nullable=True,
        doc="Cumulative lectures/labs attended to date",
    )

    __table_args__ = (
        UniqueConstraint("registration_id", "revision_number", name="uq_mca_attendance_reg_rev"),
        CheckConstraint("revision_number >= 1", name="ck_mca_attendance_revision_positive"),
        CheckConstraint(
            "attendance_percentage IS NULL OR (attendance_percentage >= 0.00 AND attendance_percentage <= 100.00)",
            name="ck_mca_attendance_pct_range",
        ),
    )

    # Relationships
    registration = relationship("MCACourseRegistration", back_populates="attendance_snapshots")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "registration_id": self.registration_id,
            "revision_number": self.revision_number,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
            "attendance_percentage": float(self.attendance_percentage) if self.attendance_percentage is not None else None,
            "classes_held": self.classes_held,
            "classes_attended": self.classes_attended,
        }

    def __repr__(self) -> str:
        return (
            f"<MCAAttendanceSnapshot(id={self.id}, reg_id={self.registration_id}, "
            f"rev={self.revision_number}, att={self.attendance_percentage}%)>"
        )


class MCAFormativeSnapshot(Base):
    """
    Point-in-time sequential snapshot of cumulative formative component marks
    for a course registration.
    """
    __tablename__ = "mca_formative_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    registration_id = Column(
        Integer,
        ForeignKey("mca_course_registrations.id", ondelete="RESTRICT"),
        nullable=False,
        doc="Parent course registration reference",
    )
    revision_number = Column(
        Integer,
        nullable=False,
        doc="Monotonically increasing revision sequence (AMD-08)",
    )
    recorded_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        doc="Physical timestamp when snapshot was captured",
    )
    mst1_marks = Column(
        Numeric(5, 2),
        nullable=True,
        doc="Mid Semester Test 1 score (0.00 to 20.00)",
    )
    mst2_marks = Column(
        Numeric(5, 2),
        nullable=True,
        doc="Mid Semester Test 2 score (0.00 to 20.00)",
    )
    assignment_score = Column(
        Numeric(5, 2),
        nullable=True,
        doc="Continuous tutorial/assignment score (0.00 to 10.00)",
    )
    viva_marks = Column(
        Numeric(5, 2),
        nullable=True,
        doc="Internal viva/lab test score (0.00 to 20.00)",
    )
    lab_record_score = Column(
        Numeric(5, 2),
        nullable=True,
        doc="Practical journal score (0.00 to 10.00)",
    )

    __table_args__ = (
        UniqueConstraint("registration_id", "revision_number", name="uq_mca_formative_reg_rev"),
        CheckConstraint("revision_number >= 1", name="ck_mca_formative_revision_positive"),
    )

    # Relationships
    registration = relationship("MCACourseRegistration", back_populates="formative_snapshots")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "registration_id": self.registration_id,
            "revision_number": self.revision_number,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
            "mst1_marks": float(self.mst1_marks) if self.mst1_marks is not None else None,
            "mst2_marks": float(self.mst2_marks) if self.mst2_marks is not None else None,
            "assignment_score": float(self.assignment_score) if self.assignment_score is not None else None,
            "viva_marks": float(self.viva_marks) if self.viva_marks is not None else None,
            "lab_record_score": float(self.lab_record_score) if self.lab_record_score is not None else None,
        }

    def __repr__(self) -> str:
        return (
            f"<MCAFormativeSnapshot(id={self.id}, reg_id={self.registration_id}, "
            f"rev={self.revision_number}, mst1={self.mst1_marks}, mst2={self.mst2_marks})>"
        )


class MCAProjectMilestoneSnapshot(Base):
    """
    Point-in-time sequential snapshot of Semester 3 Minor Project milestones.
    """
    __tablename__ = "mca_project_milestone_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    registration_id = Column(
        Integer,
        ForeignKey("mca_course_registrations.id", ondelete="RESTRICT"),
        nullable=False,
        doc="Parent course registration reference",
    )
    revision_number = Column(
        Integer,
        nullable=False,
        doc="Monotonically increasing revision sequence (AMD-09)",
    )
    recorded_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        doc="Physical timestamp when snapshot was captured",
    )
    synopsis_approved = Column(
        Boolean,
        nullable=True,
        doc="Formal problem statement approval flag",
    )
    design_score = Column(
        Numeric(5, 2),
        nullable=True,
        doc="Architecture & database review score (0.00 to 10.00)",
    )
    implementation_pct = Column(
        Numeric(5, 2),
        nullable=True,
        doc="Verified code progress percentage (0.00 to 100.00)",
    )
    supervisor_score = Column(
        Numeric(5, 2),
        nullable=True,
        doc="Guide interaction & regularity score (0.00 to 10.00)",
    )

    __table_args__ = (
        UniqueConstraint("registration_id", "revision_number", name="uq_mca_milestone_reg_rev"),
        CheckConstraint("revision_number >= 1", name="ck_mca_milestone_revision_positive"),
    )

    # Relationships
    registration = relationship("MCACourseRegistration", back_populates="milestone_snapshots")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "registration_id": self.registration_id,
            "revision_number": self.revision_number,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
            "synopsis_approved": self.synopsis_approved,
            "design_score": float(self.design_score) if self.design_score is not None else None,
            "implementation_pct": float(self.implementation_pct) if self.implementation_pct is not None else None,
            "supervisor_score": float(self.supervisor_score) if self.supervisor_score is not None else None,
        }

    def __repr__(self) -> str:
        return (
            f"<MCAProjectMilestoneSnapshot(id={self.id}, reg_id={self.registration_id}, "
            f"rev={self.revision_number}, synopsis={self.synopsis_approved}, progress={self.implementation_pct}%)>"
        )
