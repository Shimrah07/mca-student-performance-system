"""
backend/tests/test_mca_curriculum.py

Automated tests for Phase 1: MCA Curriculum Formalisation.

Covers:
- Four semesters being returned.
- All 26 courses being represented.
- Correct Semester 3 elective associations.
- Missing/unverified course codes and credits represented safely.
- Invalid semester and course-type values being rejected.
- MCA schemas accepting valid requests and rejecting invalid requests.
"""

import pytest
from pydantic import ValidationError

from app.constants.mca_curriculum import (
    MCA_PROGRAM_METADATA,
    MCA_SEMESTERS_DATA,
    get_all_mca_courses,
    get_mca_course_by_id,
    get_mca_courses_by_semester,
    get_mca_curriculum,
    get_mca_electives_by_semester,
)
from app.schemas.mca import (
    LabAcademicFeatures,
    McaAcademicFeatures,
    McaCourseGradeInput,
    McaCourseMetadata,
    McaCourseType,
    McaCurriculumResponse,
    McaPredictionResponse,
    McaScenario,
    McaSemester,
    McaSemesterMetadata,
    McaSemesterPredictionRequest,
    McaSubjectPredictionRequest,
    PredictionScope,
    PreviousDegree,
    ProjectAcademicFeatures,
    TheoryAcademicFeatures,
    VerificationStatus,
)


# ===========================================================================
# 1. Four Semesters Being Returned
# ===========================================================================

def test_four_semesters_returned_in_curriculum():
    """
    Test that the MCA curriculum definition returns exactly four semesters
    numbered 1, 2, 3, 4.
    """
    curriculum: McaCurriculumResponse = get_mca_curriculum()

    assert curriculum.total_semesters == 4
    assert len(curriculum.semesters) == 4

    semester_numbers = [sem.semester_number for sem in curriculum.semesters]
    assert semester_numbers == [1, 2, 3, 4]

    # Verify each semester object contains valid metadata
    for sem in curriculum.semesters:
        assert isinstance(sem, McaSemesterMetadata)
        assert sem.semester_number in [1, 2, 3, 4]
        assert sem.name == f"Semester {sem.semester_number}"
        assert sem.total_courses == len(sem.courses)
        assert sem.total_courses > 0


# ===========================================================================
# 2. All 26 Courses Being Represented
# ===========================================================================

def test_all_26_courses_represented():
    """
    Test that exactly 26 courses are defined across all four semesters,
    with confirmed course counts per semester:
    Sem 1: 7, Sem 2: 7, Sem 3: 7, Sem 4: 5.
    """
    all_courses = get_all_mca_courses()
    assert len(all_courses) == 26

    # Verify counts per semester
    sem1_courses = get_mca_courses_by_semester(1)
    sem2_courses = get_mca_courses_by_semester(2)
    sem3_courses = get_mca_courses_by_semester(3)
    sem4_courses = get_mca_courses_by_semester(4)

    assert len(sem1_courses) == 7
    assert len(sem2_courses) == 7
    assert len(sem3_courses) == 7
    assert len(sem4_courses) == 5

    # Verify all course IDs are unique
    course_ids = [c.id for c in all_courses]
    assert len(course_ids) == len(set(course_ids)), "Course IDs must be unique"

    # Verify all course names are non-empty
    for course in all_courses:
        assert isinstance(course.name, str)
        assert len(course.name.strip()) > 0
        assert course.semester in [1, 2, 3, 4]


def test_confirmed_course_names_exist():
    """
    Verify the confirmed subjects from each semester exist in the curriculum.
    """
    all_courses = get_all_mca_courses()
    course_name_map = {c.name: c for c in all_courses}

    expected_sem1 = [
        "Operating System",
        "Programming and Problem Solving in C",
        "Mathematical Foundation",
        "Fundamentals of Computer Technologies",
        "Technical Communication",
        "Programming and Problem Solving in C Lab",
        "Operating System Lab",
    ]
    for name in expected_sem1:
        assert name in course_name_map
        assert course_name_map[name].semester == 1

    expected_sem2 = [
        "Database Management System",
        "Computer Network",
        "Object Oriented Programming with Java",
        "Software Engineering and UML",
        "Algorithm Design",
        "Java and OOPS Lab",
        "DBMS Lab",
    ]
    for name in expected_sem2:
        assert name in course_name_map
        assert course_name_map[name].semester == 2

    expected_sem3 = [
        "Data Mining",
        "Artificial Intelligence",
        "Elective-I: Python Programming",
        "Elective-II: Machine Learning and Deep Learning",
        "Elective-III: Distributed Systems",
        "Minor Project",
        "Elective-I Lab",
    ]
    for name in expected_sem3:
        assert name in course_name_map
        assert course_name_map[name].semester == 3

    expected_sem4 = [
        "Cloud Computing Technologies",
        "Cryptocurrency and Blockchain Technologies",
        "Advanced Python",
        "Information Security",
        "Big Data Analytics",
    ]
    for name in expected_sem4:
        assert name in course_name_map
        assert course_name_map[name].semester == 4


# ===========================================================================
# 3. Correct Semester 3 Elective Associations
# ===========================================================================

def test_semester_3_elective_associations():
    """
    Test confirmed Semester 3 elective associations:
    - Elective-I = Python Programming
    - Elective-II = Machine Learning and Deep Learning
    - Elective-III = Distributed Systems
    - Elective-I Lab = Lab aligned with Elective-I
    - Minor Project = Project archetype
    """
    sem3_courses = get_mca_courses_by_semester(3)
    course_by_name = {c.name: c for c in sem3_courses}

    # Elective-I
    elec1 = course_by_name["Elective-I: Python Programming"]
    assert elec1.course_type == McaCourseType.ELECTIVE
    assert elec1.elective_group == "Elective-I"

    # Elective-II
    elec2 = course_by_name["Elective-II: Machine Learning and Deep Learning"]
    assert elec2.course_type == McaCourseType.ELECTIVE
    assert elec2.elective_group == "Elective-II"

    # Elective-III
    elec3 = course_by_name["Elective-III: Distributed Systems"]
    assert elec3.course_type == McaCourseType.ELECTIVE
    assert elec3.elective_group == "Elective-III"

    # Elective-I Lab
    elec1_lab = course_by_name["Elective-I Lab"]
    assert elec1_lab.course_type == McaCourseType.LAB
    assert elec1_lab.elective_group == "Elective-I"

    # Minor Project
    minor_proj = course_by_name["Minor Project"]
    assert minor_proj.course_type == McaCourseType.PROJECT

    # Helper filter for electives
    electives = get_mca_electives_by_semester(3)
    assert len(electives) == 3
    assert {e.elective_group for e in electives} == {"Elective-I", "Elective-II", "Elective-III"}


# ===========================================================================
# 4. Missing/Unverified Course Codes Represented Safely
# ===========================================================================

def test_semester_1_and_3_verified_codes_and_credits():
    """
    Verify that Semester 1 and Semester 3 courses contain verified official codes
    and credits from the official schemes, and verification_status == CONFIRMED.
    """
    # Semester 1 expected codes and credits
    sem1_expected = {
        "mca_sem1_os": ("MCA108", 4),
        "mca_sem1_c_prog": ("MCA109", 4),
        "mca_sem1_math": ("MCA110", 4),
        "mca_sem1_fct": ("MCA111", 4),
        "mca_sem1_tc": ("MCA112", 4),
        "mca_sem1_c_lab": ("MCA113", 8),
        "mca_sem1_os_lab": ("MCA114", 4),
    }
    sem1_courses = get_mca_courses_by_semester(1)
    assert len(sem1_courses) == 7
    for course in sem1_courses:
        assert course.id in sem1_expected
        expected_code, expected_credits = sem1_expected[course.id]
        assert course.code == expected_code
        assert course.credits == expected_credits
        assert course.verification_status == VerificationStatus.CONFIRMED

    # Semester 3 expected codes and credits
    sem3_expected = {
        "mca_sem3_dm": ("MCA301", 4),
        "mca_sem3_ai": ("MCA302", 4),
        "mca_sem3_elec1_python": ("MCA303", 4),
        "mca_sem3_elec2_mldl": ("MCA304", 4),
        "mca_sem3_elec3_ds": ("MCA305", 4),
        "mca_sem3_minor_proj": ("MCA306", 8),
        "mca_sem3_elec1_lab": ("MCA307", 4),
    }
    sem3_courses = get_mca_courses_by_semester(3)
    assert len(sem3_courses) == 7
    for course in sem3_courses:
        assert course.id in sem3_expected
        expected_code, expected_credits = sem3_expected[course.id]
        assert course.code == expected_code
        assert course.credits == expected_credits
        assert course.verification_status == VerificationStatus.CONFIRMED


def test_semester_2_and_4_unverified_codes_and_credits_are_none():
    """
    Verify that unverified course codes and credits in Semesters 2 and 4 are
    represented safely as None (not fabricated) and verification_status reflects
    pending scheme.
    """
    sem2_and_4_courses = get_mca_courses_by_semester(2) + get_mca_courses_by_semester(4)
    assert len(sem2_and_4_courses) == 12  # 7 in Sem 2, 5 in Sem 4

    for course in sem2_and_4_courses:
        assert course.code is None, f"Course {course.name} has fabricated code: {course.code}"
        assert course.credits is None, f"Course {course.name} has fabricated credits: {course.credits}"
        assert course.verification_status == VerificationStatus.SYLLABUS_CONFIRMED

        # Serialization to dict and JSON works cleanly with nullable fields
        dumped = course.model_dump()
        assert dumped["code"] is None
        assert dumped["credits"] is None

        json_str = course.model_dump_json()
        assert '"code":null' in json_str
        assert '"credits":null' in json_str



def test_course_metadata_creation_with_and_without_code():
    """
    Test creating McaCourseMetadata safely with None or verified code/credits.
    """
    # Safe with None
    course_unverified = McaCourseMetadata(
        id="sample_course",
        name="Sample Course",
        code=None,
        semester=1,
        course_type=McaCourseType.THEORY,
        credits=None,
    )
    assert course_unverified.code is None
    assert course_unverified.credits is None

    # Safe with confirmed future code
    course_verified = McaCourseMetadata(
        id="sample_course_verified",
        name="Sample Course",
        code="MCA-101",
        semester=1,
        course_type=McaCourseType.THEORY,
        credits=4,
        verification_status=VerificationStatus.CONFIRMED,
    )
    assert course_verified.code == "MCA-101"
    assert course_verified.credits == 4


# ===========================================================================
# 5. Invalid Semester and Course-Type Values Being Rejected
# ===========================================================================

def test_invalid_semester_rejected():
    """
    Test that invalid semester values (0, 5, -1, 10) are rejected by Pydantic.
    """
    # Test semester 0 in McaCourseMetadata
    with pytest.raises(ValidationError):
        McaCourseMetadata(
            id="invalid_sem",
            name="Invalid Sem Course",
            semester=0,  # ge=1
            course_type=McaCourseType.THEORY,
        )

    # Test semester 5 in McaCourseMetadata
    with pytest.raises(ValidationError):
        McaCourseMetadata(
            id="invalid_sem",
            name="Invalid Sem Course",
            semester=5,  # le=4
            course_type=McaCourseType.THEORY,
        )

    # Test semester in McaSemesterMetadata
    with pytest.raises(ValidationError):
        McaSemesterMetadata(
            semester_number=0,
            name="Invalid Semester",
            total_courses=1,
        )

    # Test semester in McaSubjectPredictionRequest
    with pytest.raises(ValidationError):
        McaSubjectPredictionRequest(
            semester=5,
            course_id="mca_sem1_os",
            course_type=McaCourseType.THEORY,
            features=McaAcademicFeatures(attendance_percentage=85.0),
        )


def test_invalid_course_type_rejected():
    """
    Test that invalid course-type values are rejected.
    """
    with pytest.raises(ValidationError):
        McaCourseMetadata(
            id="invalid_type",
            name="Invalid Type Course",
            semester=1,
            course_type="internship",  # Not in McaCourseType enum
        )

    with pytest.raises(ValidationError):
        McaSubjectPredictionRequest(
            semester=1,
            course_id="mca_sem1_os",
            course_type="unknown_type",
            features=McaAcademicFeatures(),
        )


# ===========================================================================
# 6. MCA Schemas Accepting Valid and Rejecting Invalid Requests
# ===========================================================================

def test_subject_prediction_request_scenario_a_valid():
    """
    Test valid Scenario A (Early-Warning) request for theory subject.
    """
    req = McaSubjectPredictionRequest(
        semester=1,
        course_id="mca_sem1_os",
        course_name="Operating System",
        course_type=McaCourseType.THEORY,
        scenario=McaScenario.SCENARIO_A,
        features=McaAcademicFeatures(
            attendance_percentage=82.5,
            prior_cgpa=7.8,
            active_backlogs=0,
            previous_degree=PreviousDegree.BCA,
            has_math_background=True,
        ),
        student_code="STUDENT_MCA_001",
    )
    assert req.semester == 1
    assert req.course_type == McaCourseType.THEORY
    assert req.scenario == McaScenario.SCENARIO_A
    assert req.features.attendance_percentage == 82.5


def test_subject_prediction_request_scenario_b_valid():
    """
    Test valid Scenario B (Mid-Term) request for theory subject with MST scores.
    """
    req = McaSubjectPredictionRequest(
        semester=1,
        course_id="mca_sem1_os",
        course_name="Operating System",
        course_type=McaCourseType.THEORY,
        scenario=McaScenario.SCENARIO_B,
        features=McaAcademicFeatures(
            attendance_percentage=78.0,
            mid_sem_1_marks=16.5,
            assignment_score=8.5,
        ),
    )
    assert req.scenario == McaScenario.SCENARIO_B
    assert req.features.mid_sem_1_marks == 16.5


def test_subject_prediction_request_scenario_b_missing_midterm_fails():
    """
    Test that Scenario B for theory courses requires at least one mid-sem score.
    """
    with pytest.raises(ValidationError) as exc_info:
        McaSubjectPredictionRequest(
            semester=1,
            course_id="mca_sem1_os",
            course_name="Operating System",
            course_type=McaCourseType.THEORY,
            scenario=McaScenario.SCENARIO_B,
            features=McaAcademicFeatures(
                attendance_percentage=78.0,
                mid_sem_1_marks=None,
                mid_sem_2_marks=None,
            ),
        )
    assert "Scenario B (Mid-Term) for theory/elective courses requires at least one Mid-Semester Test score" in str(exc_info.value)


def test_lab_course_scenario_b_without_mst_allowed():
    """
    Test that practical lab courses do NOT require theory mid-sem marks for Scenario B.
    """
    req = McaSubjectPredictionRequest(
        semester=1,
        course_id="mca_sem1_os_lab",
        course_name="Operating System Lab",
        course_type=McaCourseType.LAB,
        scenario=McaScenario.SCENARIO_B,
        features=McaAcademicFeatures(
            lab_attendance_percentage=90.0,
            experiments_completed=10,
            total_experiments=12,
            internal_viva_marks=17.0,
            lab_record_score=8.5,
        ),
    )
    assert req.course_type == McaCourseType.LAB
    assert req.features.experiments_completed == 10


def test_academic_features_bounds_validation():
    """
    Test validation bounds on marks, attendance, and GPA.
    """
    # Attendance > 100% rejected
    with pytest.raises(ValidationError):
        McaAcademicFeatures(attendance_percentage=105.0)

    # Attendance < 0% rejected
    with pytest.raises(ValidationError):
        McaAcademicFeatures(attendance_percentage=-5.0)

    # Mid Sem > 20 marks rejected
    with pytest.raises(ValidationError):
        McaAcademicFeatures(mid_sem_1_marks=25.0)

    # Assignment score > 10 marks rejected
    with pytest.raises(ValidationError):
        McaAcademicFeatures(assignment_score=15.0)

    # Prior CGPA > 10 rejected
    with pytest.raises(ValidationError):
        McaAcademicFeatures(prior_cgpa=11.0)


def test_semester_prediction_request_valid():
    """
    Test valid semester-level prediction request with a list of enrolled courses.
    """
    roster = [
        McaCourseGradeInput(
            course_id="mca_sem1_os",
            course_name="Operating System",
            course_type=McaCourseType.THEORY,
            internal_marks=80.0,
            attendance_percentage=85.0,
        ),
        McaCourseGradeInput(
            course_id="mca_sem1_c_prog",
            course_name="Programming and Problem Solving in C",
            course_type=McaCourseType.THEORY,
            internal_marks=75.0,
            attendance_percentage=80.0,
        ),
    ]

    req = McaSemesterPredictionRequest(
        semester=1,
        scenario=McaScenario.SCENARIO_A,
        courses=roster,
        overall_attendance=82.5,
        prior_cgpa=8.0,
    )
    assert req.semester == 1
    assert len(req.courses) == 2


def test_semester_prediction_request_empty_courses_rejected():
    """
    Test that an empty courses list is rejected.
    """
    with pytest.raises(ValidationError):
        McaSemesterPredictionRequest(
            semester=1,
            scenario=McaScenario.SCENARIO_A,
            courses=[],  # min_length=1
        )


def test_mca_prediction_response_schema():
    """
    Test that McaPredictionResponse validates and serializes correctly,
    including the pedagogical disclaimer and safeguard note.
    """
    resp = McaPredictionResponse(
        prediction_scope=PredictionScope.SUBJECT,
        semester=1,
        course_id="mca_sem1_os",
        course_name="Operating System",
        course_type=McaCourseType.THEORY,
        scenario="Scenario A",
        predicted_tier="Good",
        estimated_score_range="65% – 79%",
        prediction_probabilities={"Excellent": 0.20, "Good": 0.65, "Average": 0.15},
        summary="Consistent attendance and strong foundations indicate solid progress.",
        actionable_recommendations=[
            "Maintain current lecture attendance above 80%.",
            "Prepare for upcoming Mid-Semester Test 1 focusing on process scheduling.",
        ],
        strengths_identified=["Regular lecture attendance", "Active participation"],
        evaluated_factors={"attendance_percentage": 82.5, "prior_cgpa": 7.8},
        persisted=False,
    )

    assert resp.predicted_tier == "Good"
    assert "Supportive academic feedback" in resp.academic_safeguards_note
    assert "Probabilities are uncalibrated" in resp.probabilities_note

    dumped = resp.model_dump()
    assert dumped["predicted_tier"] == "Good"
    assert dumped["persisted"] is False


def test_specialized_feature_schemas():
    """
    Test TheoryAcademicFeatures, LabAcademicFeatures, and ProjectAcademicFeatures.
    """
    theory = TheoryAcademicFeatures(
        attendance_percentage=85.0,
        mid_sem_1_marks=17.0,
        mid_sem_2_marks=18.0,
        assignment_score=9.0,
        prior_cgpa=8.2,
        active_backlogs=0,
        previous_degree=PreviousDegree.BCA,
        has_math_background=True,
        weekly_study_hours=12.0,
    )
    assert theory.attendance_percentage == 85.0
    assert theory.weekly_study_hours == 12.0

    lab = LabAcademicFeatures(
        lab_attendance_percentage=95.0,
        experiments_completed=10,
        total_experiments=10,
        internal_viva_marks=19.0,
        lab_record_score=9.5,
        prior_coding_experience=True,
    )
    assert lab.experiments_completed == 10

    project = ProjectAcademicFeatures(
        synopsis_approved=True,
        literature_survey_score=8.5,
        design_approval_score=9.0,
        implementation_progress_pct=75.0,
        supervisor_interaction_score=9.5,
    )
    assert project.synopsis_approved is True
    assert project.implementation_progress_pct == 75.0
