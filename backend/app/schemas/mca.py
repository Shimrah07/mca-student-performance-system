"""
backend/app/schemas/mca.py

Pydantic schemas for the Master of Computer Applications (MCA) curriculum,
subject metadata, academic assessment inputs, and prediction requests/responses
for UIT-RGPV (Autonomous), Bhopal.

Design Principles:
- Additive module: does NOT modify or replace existing UCI benchmark schemas.
- Modular course archetypes: Theory, Lab, Elective, Project.
- Flexible academic indicators: MST scores, lab viva, assignment completion, attendance %.
- Does NOT hardcode 80%/65%/50% thresholds or the 75% attendance rule as official RGPV regulations.
- Reusable metadata schemas for curriculum discovery and prediction workflows.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class McaSemester(int, Enum):
    SEMESTER_1 = 1
    SEMESTER_2 = 2
    SEMESTER_3 = 3
    SEMESTER_4 = 4


class McaCourseType(str, Enum):
    THEORY = "theory"
    LAB = "lab"
    ELECTIVE = "elective"
    PROJECT = "project"


class PredictionScope(str, Enum):
    SUBJECT = "subject"
    SEMESTER = "semester"


class McaScenario(str, Enum):
    SCENARIO_A = "Scenario A"  # Early-Warning / Formative
    SCENARIO_B = "Scenario B"  # Mid-Term / Continuous Evaluation


class VerificationStatus(str, Enum):
    SYLLABUS_CONFIRMED = "syllabus_confirmed_code_pending"
    CONFIRMED = "confirmed"
    UNVERIFIED = "unverified"


class PreviousDegree(str, Enum):
    BCA = "BCA"
    BSC_CS = "B.Sc Computer Science"
    BSC_IT = "B.Sc IT"
    BSC_OTHER = "B.Sc Other / Mathematics"
    BCOM_BA_OTHER = "B.Com / B.A / Other"
    OTHER = "Other"


# ---------------------------------------------------------------------------
# Curriculum & Course Metadata Schemas
# ---------------------------------------------------------------------------

class McaCourseMetadata(BaseModel):
    """
    Metadata representation of a single MCA course.
    """
    id: str = Field(..., description="Unique slug identifier (e.g. 'mca_sem1_os')")
    name: str = Field(..., description="Official title of the subject/lab")
    code: Optional[str] = Field(None, description="Official course code; nullable where unverified")
    semester: int = Field(..., ge=1, le=4, description="Semester number (1-4)")
    course_type: McaCourseType = Field(..., description="Course archetype: theory, lab, elective, project")
    elective_group: Optional[str] = Field(None, description="Elective cluster identifier (e.g. 'Elective-I')")
    credits: Optional[int] = Field(None, ge=1, le=12, description="Course credit value; nullable where unverified")
    source_scheme: str = Field(
        "UIT-RGPV (Autonomous) MCA Curriculum",
        description="Source curriculum scheme",
    )
    effective_date: str = Field("2026-27", description="Curriculum effective academic session")
    verification_status: VerificationStatus = Field(
        VerificationStatus.SYLLABUS_CONFIRMED,
        description="Verification audit status of code and credits",
    )
    verification_notes: Optional[str] = Field(
        None,
        description="Audit commentary regarding code and credit verification",
    )


class McaSemesterMetadata(BaseModel):
    """
    Curriculum structure for a single semester.
    """
    semester_number: int = Field(..., ge=1, le=4)
    name: str = Field(...)
    academic_focus: Optional[str] = Field(None)
    total_courses: int = Field(..., ge=1)
    courses: List[McaCourseMetadata] = Field(default_factory=list)


class McaCurriculumResponse(BaseModel):
    """
    Comprehensive MCA curriculum payload returned to clients.
    """
    program_name: str = "Master of Computer Applications"
    program_code: str = "MCA"
    institution: str = "University Institute of Technology — RGPV (Autonomous), Bhopal"
    department: str = "Department of Computer Applications"
    total_semesters: int = 4
    total_courses: int = 26
    semesters: List[McaSemesterMetadata] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Differentiated Subject-Specific Academic Features
# ---------------------------------------------------------------------------

class TheoryAcademicFeatures(BaseModel):
    """
    Formative academic indicators for classroom theory courses.
    """
    attendance_percentage: Optional[float] = Field(
        None, ge=0.0, le=100.0, description="Lecture attendance percentage"
    )
    mid_sem_1_marks: Optional[float] = Field(
        None, ge=0.0, le=20.0, description="Mid Semester Test 1 score (typically out of 20)"
    )
    mid_sem_2_marks: Optional[float] = Field(
        None, ge=0.0, le=20.0, description="Mid Semester Test 2 score (typically out of 20)"
    )
    assignment_score: Optional[float] = Field(
        None, ge=0.0, le=10.0, description="Continuous assignment / tutorial assessment score"
    )
    prior_cgpa: Optional[float] = Field(
        None, ge=0.0, le=10.0, description="Prior cumulative GPA on 10-point scale (applicable for Sem 2, 3, 4)"
    )
    active_backlogs: Optional[int] = Field(
        0, ge=0, description="Number of currently uncleared backlogs"
    )
    previous_degree: Optional[PreviousDegree] = Field(
        None, description="Undergraduate background degree"
    )
    has_math_background: Optional[bool] = Field(
        None, description="Formal mathematics background at 10+2 or UG level"
    )
    weekly_study_hours: Optional[float] = Field(
        None, ge=0.0, le=80.0, description="Self-reported weekly independent study hours for this course"
    )


class LabAcademicFeatures(BaseModel):
    """
    Formative academic indicators for practical / laboratory courses.
    """
    lab_attendance_percentage: Optional[float] = Field(
        None, ge=0.0, le=100.0, description="Laboratory attendance percentage"
    )
    experiments_completed: Optional[int] = Field(
        None, ge=0, description="Number of certified lab experiments completed"
    )
    total_experiments: Optional[int] = Field(
        None, ge=1, description="Total prescribed lab experiments in syllabus"
    )
    internal_viva_marks: Optional[float] = Field(
        None, ge=0.0, le=20.0, description="Continuous internal lab viva score"
    )
    lab_record_score: Optional[float] = Field(
        None, ge=0.0, le=10.0, description="Practical file / lab journal evaluation score"
    )
    prior_coding_experience: Optional[bool] = Field(
        None, description="Prior familiarity with the course programming language"
    )


class ProjectAcademicFeatures(BaseModel):
    """
    Formative milestone indicators for the Semester 3 Minor Project.
    """
    synopsis_approved: Optional[bool] = Field(
        None, description="Formal approval of project synopsis and problem statement"
    )
    literature_survey_score: Optional[float] = Field(
        None, ge=0.0, le=10.0, description="Literature review / background research quality score"
    )
    design_approval_score: Optional[float] = Field(
        None, ge=0.0, le=10.0, description="System architecture and database design review score"
    )
    implementation_progress_pct: Optional[float] = Field(
        None, ge=0.0, le=100.0, description="Guide-verified implementation progress percentage"
    )
    supervisor_interaction_score: Optional[float] = Field(
        None, ge=0.0, le=10.0, description="Faculty guide regularity and progress review score"
    )


class McaAcademicFeatures(BaseModel):
    """
    Flexible, unified container for MCA subject academic indicators.
    Allows clients to supply indicators across theory, lab, and project dimensions.
    """
    # Theory indicators
    attendance_percentage: Optional[float] = Field(None, ge=0.0, le=100.0)
    mid_sem_1_marks: Optional[float] = Field(None, ge=0.0, le=20.0)
    mid_sem_2_marks: Optional[float] = Field(None, ge=0.0, le=20.0)
    assignment_score: Optional[float] = Field(None, ge=0.0, le=10.0)

    # Practical / Lab indicators
    lab_attendance_percentage: Optional[float] = Field(None, ge=0.0, le=100.0)
    experiments_completed: Optional[int] = Field(None, ge=0)
    total_experiments: Optional[int] = Field(None, ge=1)
    internal_viva_marks: Optional[float] = Field(None, ge=0.0, le=20.0)
    lab_record_score: Optional[float] = Field(None, ge=0.0, le=10.0)

    # Project indicators
    synopsis_approved: Optional[bool] = None
    implementation_progress_pct: Optional[float] = Field(None, ge=0.0, le=100.0)

    # General background indicators
    prior_cgpa: Optional[float] = Field(None, ge=0.0, le=10.0)
    active_backlogs: Optional[int] = Field(0, ge=0)
    previous_degree: Optional[PreviousDegree] = None
    has_math_background: Optional[bool] = None

    # Custom indicators dictionary for open extensibility
    custom_indicators: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# Prediction Requests
# ---------------------------------------------------------------------------

class McaSubjectPredictionRequest(BaseModel):
    """
    Payload to request performance assessment for an individual MCA subject.
    """
    semester: int = Field(..., ge=1, le=4, description="Semester number (1 to 4)")
    course_id: str = Field(..., description="Unique course identifier (e.g. 'mca_sem1_os')")
    course_name: Optional[str] = Field(None, description="Optional human-readable subject title")
    course_type: McaCourseType = Field(..., description="Course archetype: theory, lab, elective, project")
    scenario: McaScenario = Field(
        McaScenario.SCENARIO_A,
        description="Scenario A (Early-Warning) or Scenario B (Mid-Term Diagnostic)",
    )
    features: McaAcademicFeatures = Field(..., description="Academic assessment indicators")
    student_code: Optional[str] = Field(
        None, description="Optional anonymized student identifier"
    )

    @model_validator(mode="after")
    def validate_scenario_requirements(self) -> "McaSubjectPredictionRequest":
        """
        Validate that Scenario B for theory courses receives mid-term indicators.
        """
        if self.scenario == McaScenario.SCENARIO_B and self.course_type in (McaCourseType.THEORY, McaCourseType.ELECTIVE):
            if self.features.mid_sem_1_marks is None and self.features.mid_sem_2_marks is None:
                raise ValueError(
                    "Scenario B (Mid-Term) for theory/elective courses requires at least one "
                    "Mid-Semester Test score (mid_sem_1_marks or mid_sem_2_marks)."
                )
        return self


class McaCourseGradeInput(BaseModel):
    """
    Single course status in a semester-level aggregate prediction.
    """
    course_id: str = Field(..., description="Course identifier")
    course_name: str = Field(..., description="Course title")
    course_type: McaCourseType = Field(..., description="Course type")
    internal_marks: Optional[float] = Field(None, ge=0.0, le=100.0, description="Current internal percentage")
    attendance_percentage: Optional[float] = Field(None, ge=0.0, le=100.0, description="Course attendance %")


class McaSemesterPredictionRequest(BaseModel):
    """
    Payload to request semester-level academic trajectory projection.
    """
    semester: int = Field(..., ge=1, le=4, description="Semester number (1 to 4)")
    scenario: McaScenario = Field(McaScenario.SCENARIO_A)
    courses: List[McaCourseGradeInput] = Field(
        ..., min_length=1, max_length=12, description="Roster of enrolled courses in the semester"
    )
    overall_attendance: Optional[float] = Field(None, ge=0.0, le=100.0)
    prior_cgpa: Optional[float] = Field(None, ge=0.0, le=10.0)
    active_backlogs: Optional[int] = Field(0, ge=0)
    student_code: Optional[str] = None


# ---------------------------------------------------------------------------
# Prediction Response
# ---------------------------------------------------------------------------

class McaPredictionResponse(BaseModel):
    """
    Standardized response payload for MCA predictions and supportive guidance.
    """
    prediction_scope: PredictionScope = Field(..., description="Scope: 'subject' or 'semester'")
    semester: int = Field(..., ge=1, le=4)
    course_id: Optional[str] = Field(None, description="Course ID if subject-level prediction")
    course_name: Optional[str] = Field(None, description="Course title if subject-level prediction")
    course_type: Optional[McaCourseType] = Field(None)
    scenario: str = Field(...)
    predicted_tier: str = Field(
        ...,
        description="Predicted performance tier (e.g. 'Excellent', 'Good', 'Average', 'Needs Improvement')",
    )
    estimated_score_range: Optional[str] = Field(
        None, description="Indicative performance range based on formative inputs"
    )
    prediction_probabilities: Optional[Dict[str, float]] = Field(
        None, description="Indicative uncalibrated class probability distribution"
    )
    probabilities_note: str = Field(
        "Indicative model estimates only. Probabilities are uncalibrated and do not represent guaranteed academic results.",
        description="Pedagogical disclaimer regarding probabilistic outputs",
    )
    summary: str = Field(..., description="Strategic academic guidance summary")
    actionable_recommendations: List[str] = Field(..., description="Actionable recommendations")
    strengths_identified: List[str] = Field(..., description="Positive academic commitments recognized")
    evaluated_factors: Dict[str, Any] = Field(..., description="Input factors evaluated")
    academic_safeguards_note: str = Field(
        "Supportive academic feedback. Not an official RGPV examination result or detention notice.",
        description="Pedagogical and institutional safeguard notice",
    )
    prediction_id: Optional[int] = Field(None, description="Database record ID if persisted")
    persisted: bool = Field(False, description="True if saved to database")
    created_at: Optional[datetime] = Field(None)


# ---------------------------------------------------------------------------
# Phase 3B Point-in-Time Prediction API Schemas
# ---------------------------------------------------------------------------

class McaSubjectPredictionApiRequest(BaseModel):
    """
    Request schema for subject-level point-in-time performance prediction.
    Features are extracted from historical snapshots at or before cutoff_timestamp.
    """
    registration_id: int = Field(..., gt=0, description="MCA Course Registration ID")
    cutoff_timestamp: datetime = Field(
        ...,
        description="Explicit point-in-time freshness cutoff timestamp (required; never defaulted to current time)",
    )
    student_id: Optional[int] = Field(
        None,
        gt=0,
        description="Optional student ID for cross-validation against the registration",
    )


class McaSemesterPredictionApiRequest(BaseModel):
    """
    Request schema for semester-level point-in-time performance prediction.
    Features are extracted across all enrolled courses in target_semester at or before cutoff_timestamp.
    """
    student_id: int = Field(..., gt=0, description="MCA Student ID")
    target_semester: int = Field(..., ge=1, le=4, description="Target MCA semester (1 to 4)")
    cutoff_timestamp: datetime = Field(
        ...,
        description="Explicit point-in-time freshness cutoff timestamp (required; never defaulted to current time)",
    )


class McaPredictionApiResponse(BaseModel):
    """
    Standardized response schema for point-in-time MCA predictions.
    Includes classification outcome, confidence, class probabilities,
    audit metadata, input feature snapshot, and mandatory synthetic disclaimer.
    """
    prediction_id: int = Field(..., description="Unique database ID of persisted prediction record")
    scope: str = Field(..., description="Prediction scope: 'subject' or 'semester'")
    student_id: Optional[int] = Field(None, description="Associated student ID")
    registration_id: Optional[int] = Field(None, description="Course registration ID (subject-level)")
    course_id: Optional[int] = Field(None, description="Course ID (subject-level)")
    course_code: Optional[str] = Field(None, description="Official course code if available")
    course_name: Optional[str] = Field(None, description="Course title if available")
    target_semester: int = Field(..., ge=1, le=4, description="Target semester evaluated")
    predicted_tier: str = Field(
        ...,
        description="Predicted performance tier ('Excellent', 'Good', 'Average', 'Needs Improvement')",
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Predicted class probability/confidence")
    probabilities: Dict[str, float] = Field(
        ...,
        description="Class probability distribution across performance tiers",
    )
    cutoff_timestamp: datetime = Field(..., description="Point-in-time evaluation boundary")
    model_name: str = Field(..., description="Model identifier used for inference")
    model_version: str = Field(..., description="Model release version")
    input_snapshot_json: Dict[str, Any] = Field(..., description="Deterministic extracted features snapshot")
    synthetic_data_warning: str = Field(..., description="Mandatory synthetic prototype data disclaimer")
    created_at: datetime = Field(..., description="Record creation timestamp in database")

