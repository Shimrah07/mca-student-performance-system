"""
backend/app/models/mca/curriculum.py

MCA Curriculum, Program, Course, Academic Session, and Session Course Models.
Adheres strictly to the Phase 2B Final Implementation Contract.
"""

from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base


class MCAProgram(Base):
    """
    Top-level master representing the academic program (e.g. MCA).
    """
    __tablename__ = "mca_programs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    program_name = Column(String(100), nullable=False, doc="Official program name")
    program_code = Column(String(20), nullable=False, doc="Unique program code (e.g. 'MCA')")
    duration_semesters = Column(Integer, nullable=False, default=4, doc="Standard duration in semesters")
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        doc="Record creation timestamp",
    )

    __table_args__ = (
        UniqueConstraint("program_code", name="uq_mca_program_code"),
    )

    # Relationships
    schemes = relationship("MCACurriculumScheme", back_populates="program", passive_deletes=True)
    courses = relationship("MCACourse", back_populates="program", passive_deletes=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "program_name": self.program_name,
            "program_code": self.program_code,
            "duration_semesters": self.duration_semesters,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<MCAProgram(id={self.id}, code='{self.program_code}', name='{self.program_name}')>"


class MCACurriculumScheme(Base):
    """
    Versioned curriculum syllabus under an academic program.
    """
    __tablename__ = "mca_curriculum_schemes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    program_id = Column(
        Integer,
        ForeignKey("mca_programs.id", ondelete="RESTRICT"),
        nullable=False,
        doc="Parent program reference",
    )
    scheme_name = Column(String(100), nullable=False, doc="Scheme name (e.g. UIT-RGPV Autonomous MCA Scheme)")
    scheme_code = Column(String(50), nullable=False, doc="Unique scheme code (e.g. 'MCA-AUTONOMOUS-2026')")
    effective_from = Column(String(20), nullable=False, doc="Effective start session (e.g. '2026-27')")
    effective_until = Column(String(20), nullable=True, doc="Expiration session or NULL if active")
    is_active = Column(Boolean, nullable=False, default=True, doc="Active scheme flag")
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        doc="Record creation timestamp",
    )

    __table_args__ = (
        UniqueConstraint("scheme_code", name="uq_mca_scheme_code"),
    )

    # Relationships
    program = relationship("MCAProgram", back_populates="schemes")
    courses = relationship("MCACourse", back_populates="scheme", passive_deletes=True)
    sessions = relationship("MCAAcademicSession", back_populates="scheme", passive_deletes=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "program_id": self.program_id,
            "scheme_name": self.scheme_name,
            "scheme_code": self.scheme_code,
            "effective_from": self.effective_from,
            "effective_until": self.effective_until,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<MCACurriculumScheme(id={self.id}, code='{self.scheme_code}', name='{self.scheme_name}')>"


class MCACourse(Base):
    """
    Master catalog of curriculum subjects across semesters.
    """
    __tablename__ = "mca_courses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    program_id = Column(
        Integer,
        ForeignKey("mca_programs.id", ondelete="RESTRICT"),
        nullable=False,
        doc="Parent program reference",
    )
    scheme_id = Column(
        Integer,
        ForeignKey("mca_curriculum_schemes.id", ondelete="RESTRICT"),
        nullable=True,
        doc="Curriculum scheme reference; nullable for provisional courses",
    )
    course_code = Column(String(20), nullable=True, doc="Official course code (e.g. 'MCA108'); nullable if pending")
    course_name = Column(String(150), nullable=False, doc="Official course title")
    semester_number = Column(Integer, nullable=False, doc="Prescribed semester (1-4)")
    course_type = Column(String(20), nullable=False, doc="Course archetype: 'theory', 'lab', 'elective', 'project'")
    elective_group = Column(String(50), nullable=True, doc="Elective cluster identifier (e.g. 'Elective-I')")
    credits = Column(Integer, nullable=True, doc="Credit value; nullable if unverified")
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        doc="Record creation timestamp",
    )

    __table_args__ = (
        UniqueConstraint("program_id", "course_code", name="uq_mca_course_program_code"),
        CheckConstraint("semester_number IN (1, 2, 3, 4)", name="ck_mca_course_semester_number"),
        CheckConstraint(
            "course_type IN ('theory', 'lab', 'elective', 'project')",
            name="ck_mca_course_type",
        ),
    )

    # Relationships
    program = relationship("MCAProgram", back_populates="courses")
    scheme = relationship("MCACurriculumScheme", back_populates="courses")
    session_courses = relationship("MCASessionCourse", back_populates="course", passive_deletes=True)
    predictions = relationship("MCAPredictionRecord", back_populates="course", passive_deletes=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "program_id": self.program_id,
            "scheme_id": self.scheme_id,
            "course_code": self.course_code,
            "course_name": self.course_name,
            "semester_number": self.semester_number,
            "course_type": self.course_type,
            "elective_group": self.elective_group,
            "credits": self.credits,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<MCACourse(id={self.id}, code='{self.course_code}', name='{self.course_name}', sem={self.semester_number})>"


class MCAAcademicSession(Base):
    """
    Specific academic batch or cohort running an approved curriculum scheme.
    """
    __tablename__ = "mca_academic_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scheme_id = Column(
        Integer,
        ForeignKey("mca_curriculum_schemes.id", ondelete="RESTRICT"),
        nullable=False,
        doc="Governing curriculum scheme reference",
    )
    session_name = Column(String(100), nullable=False, doc="Batch title (e.g. 'MCA 2025-27 Batch')")
    batch_year = Column(String(20), nullable=False, doc="Batch intake period (e.g. '2025-2027')")
    start_date = Column(Date, nullable=False, doc="Cohort commencement date")
    end_date = Column(Date, nullable=False, doc="Cohort completion date")
    is_active = Column(Boolean, nullable=False, default=True, doc="Cohort active status flag")
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        doc="Record creation timestamp",
    )

    __table_args__ = (
        UniqueConstraint("scheme_id", "session_name", name="uq_mca_session_scheme_name"),
    )

    # Relationships
    scheme = relationship("MCACurriculumScheme", back_populates="sessions")
    session_courses = relationship("MCASessionCourse", back_populates="session", passive_deletes=True)
    students = relationship("MCAStudent", back_populates="session", passive_deletes=True)
    semester_results = relationship("MCASemesterResult", back_populates="session", passive_deletes=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "scheme_id": self.scheme_id,
            "session_name": self.session_name,
            "batch_year": self.batch_year,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<MCAAcademicSession(id={self.id}, name='{self.session_name}', batch='{self.batch_year}')>"


class MCASessionCourse(Base):
    """
    Bridge table defining courses actively offered in a given academic session.
    """
    __tablename__ = "mca_session_courses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(
        Integer,
        ForeignKey("mca_academic_sessions.id", ondelete="RESTRICT"),
        nullable=False,
        doc="Academic session offering reference",
    )
    course_id = Column(
        Integer,
        ForeignKey("mca_courses.id", ondelete="RESTRICT"),
        nullable=False,
        doc="Course catalog reference",
    )

    __table_args__ = (
        UniqueConstraint("session_id", "course_id", name="uq_mca_session_course"),
    )

    # Relationships
    session = relationship("MCAAcademicSession", back_populates="session_courses")
    course = relationship("MCACourse", back_populates="session_courses")
    registrations = relationship("MCACourseRegistration", back_populates="session_course", passive_deletes=True)
    assessment_events = relationship("MCAAssessmentEvent", back_populates="session_course", passive_deletes=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "course_id": self.course_id,
        }

    def __repr__(self) -> str:
        return f"<MCASessionCourse(id={self.id}, session_id={self.session_id}, course_id={self.course_id})>"
