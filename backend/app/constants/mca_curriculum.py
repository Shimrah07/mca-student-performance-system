"""
backend/app/constants/mca_curriculum.py

Canonical MCA curriculum definition for University Institute of Technology —
RGPV (Autonomous), Bhopal, Department of Computer Applications.

Scope: 4 Semesters, 26 Confirmed Courses.

Design Rules:
- Course codes and credits are null where unverified (no fabricated values).
- No hardcoded 80%/65%/50% thresholds or 75% attendance detention rules.
- Confirmed Semester 3 electives:
    Elective-I   : Python Programming
    Elective-II  : Machine Learning and Deep Learning
    Elective-III : Distributed Systems
"""

from typing import List, Optional
from app.schemas.mca import (
    McaCourseMetadata,
    McaCourseType,
    McaCurriculumResponse,
    McaSemesterMetadata,
    VerificationStatus,
)

MCA_PROGRAM_METADATA = {
    "program_name": "Master of Computer Applications",
    "program_code": "MCA",
    "institution": "University Institute of Technology — RGPV (Autonomous), Bhopal",
    "department": "Department of Computer Applications",
    "total_semesters": 4,
    "total_courses": 26,
    "source_scheme": "UIT-RGPV (Autonomous) MCA Curriculum Roster",
    "effective_date": "2026-27",
}

MCA_SEMESTERS_DATA: List[dict] = [
    {
        "semester_number": 1,
        "name": "Semester 1",
        "academic_focus": "Computing Foundations, Programming Systems & Core Engineering",
        "courses": [
            {
                "id": "mca_sem1_os",
                "name": "Operating System",
                "code": "MCA108",
                "semester": 1,
                "course_type": McaCourseType.THEORY,
                "elective_group": None,
                "credits": 4,
                "source_scheme": "UIT-RGPV (Autonomous) MCA Curriculum",
                "effective_date": "2026-27",
                "verification_status": VerificationStatus.CONFIRMED,
                "verification_notes": "Course code and credits verified from official Semester 1 scheme.",
            },
            {
                "id": "mca_sem1_c_prog",
                "name": "Programming and Problem Solving in C",
                "code": "MCA109",
                "semester": 1,
                "course_type": McaCourseType.THEORY,
                "elective_group": None,
                "credits": 4,
                "source_scheme": "UIT-RGPV (Autonomous) MCA Curriculum",
                "effective_date": "2026-27",
                "verification_status": VerificationStatus.CONFIRMED,
                "verification_notes": "Course code and credits verified from official Semester 1 scheme.",
            },
            {
                "id": "mca_sem1_math",
                "name": "Mathematical Foundation",
                "code": "MCA110",
                "semester": 1,
                "course_type": McaCourseType.THEORY,
                "elective_group": None,
                "credits": 4,
                "source_scheme": "UIT-RGPV (Autonomous) MCA Curriculum",
                "effective_date": "2026-27",
                "verification_status": VerificationStatus.CONFIRMED,
                "verification_notes": "Course code and credits verified from official Semester 1 scheme.",
            },
            {
                "id": "mca_sem1_fct",
                "name": "Fundamentals of Computer Technologies",
                "code": "MCA111",
                "semester": 1,
                "course_type": McaCourseType.THEORY,
                "elective_group": None,
                "credits": 4,
                "source_scheme": "UIT-RGPV (Autonomous) MCA Curriculum",
                "effective_date": "2026-27",
                "verification_status": VerificationStatus.CONFIRMED,
                "verification_notes": "Course code and credits verified from official Semester 1 scheme.",
            },
            {
                "id": "mca_sem1_tc",
                "name": "Technical Communication",
                "code": "MCA112",
                "semester": 1,
                "course_type": McaCourseType.THEORY,
                "elective_group": None,
                "credits": 4,
                "source_scheme": "UIT-RGPV (Autonomous) MCA Curriculum",
                "effective_date": "2026-27",
                "verification_status": VerificationStatus.CONFIRMED,
                "verification_notes": "Course code and credits verified from official Semester 1 scheme.",
            },
            {
                "id": "mca_sem1_c_lab",
                "name": "Programming and Problem Solving in C Lab",
                "code": "MCA113",
                "semester": 1,
                "course_type": McaCourseType.LAB,
                "elective_group": None,
                "credits": 8,
                "source_scheme": "UIT-RGPV (Autonomous) MCA Curriculum",
                "effective_date": "2026-27",
                "verification_status": VerificationStatus.CONFIRMED,
                "verification_notes": "Course code and credits verified from official Semester 1 scheme (Practical Lab).",
            },
            {
                "id": "mca_sem1_os_lab",
                "name": "Operating System Lab",
                "code": "MCA114",
                "semester": 1,
                "course_type": McaCourseType.LAB,
                "elective_group": None,
                "credits": 4,
                "source_scheme": "UIT-RGPV (Autonomous) MCA Curriculum",
                "effective_date": "2026-27",
                "verification_status": VerificationStatus.CONFIRMED,
                "verification_notes": "Course code and credits verified from official Semester 1 scheme (Practical Lab).",
            },
        ],
    },
    {
        "semester_number": 2,
        "name": "Semester 2",
        "academic_focus": "Database Systems, Networking, OOP & Algorithm Design",
        "courses": [
            {
                "id": "mca_sem2_dbms",
                "name": "Database Management System",
                "code": None,
                "semester": 2,
                "course_type": McaCourseType.THEORY,
                "elective_group": None,
                "credits": None,
                "source_scheme": "UIT-RGPV (Autonomous) MCA Curriculum",
                "effective_date": "2026-27",
                "verification_status": VerificationStatus.SYLLABUS_CONFIRMED,
                "verification_notes": "Confirmed course name; official code and credits pending verification.",
            },
            {
                "id": "mca_sem2_cn",
                "name": "Computer Network",
                "code": None,
                "semester": 2,
                "course_type": McaCourseType.THEORY,
                "elective_group": None,
                "credits": None,
                "source_scheme": "UIT-RGPV (Autonomous) MCA Curriculum",
                "effective_date": "2026-27",
                "verification_status": VerificationStatus.SYLLABUS_CONFIRMED,
                "verification_notes": "Confirmed course name; official code and credits pending verification.",
            },
            {
                "id": "mca_sem2_java",
                "name": "Object Oriented Programming with Java",
                "code": None,
                "semester": 2,
                "course_type": McaCourseType.THEORY,
                "elective_group": None,
                "credits": None,
                "source_scheme": "UIT-RGPV (Autonomous) MCA Curriculum",
                "effective_date": "2026-27",
                "verification_status": VerificationStatus.SYLLABUS_CONFIRMED,
                "verification_notes": "Confirmed course name; official code and credits pending verification.",
            },
            {
                "id": "mca_sem2_se_uml",
                "name": "Software Engineering and UML",
                "code": None,
                "semester": 2,
                "course_type": McaCourseType.THEORY,
                "elective_group": None,
                "credits": None,
                "source_scheme": "UIT-RGPV (Autonomous) MCA Curriculum",
                "effective_date": "2026-27",
                "verification_status": VerificationStatus.SYLLABUS_CONFIRMED,
                "verification_notes": "Confirmed course name; official code and credits pending verification.",
            },
            {
                "id": "mca_sem2_ada",
                "name": "Algorithm Design",
                "code": None,
                "semester": 2,
                "course_type": McaCourseType.THEORY,
                "elective_group": None,
                "credits": None,
                "source_scheme": "UIT-RGPV (Autonomous) MCA Curriculum",
                "effective_date": "2026-27",
                "verification_status": VerificationStatus.SYLLABUS_CONFIRMED,
                "verification_notes": "Confirmed course name; official code and credits pending verification.",
            },
            {
                "id": "mca_sem2_java_lab",
                "name": "Java and OOPS Lab",
                "code": None,
                "semester": 2,
                "course_type": McaCourseType.LAB,
                "elective_group": None,
                "credits": None,
                "source_scheme": "UIT-RGPV (Autonomous) MCA Curriculum",
                "effective_date": "2026-27",
                "verification_status": VerificationStatus.SYLLABUS_CONFIRMED,
                "verification_notes": "Practical laboratory course.",
            },
            {
                "id": "mca_sem2_dbms_lab",
                "name": "DBMS Lab",
                "code": None,
                "semester": 2,
                "course_type": McaCourseType.LAB,
                "elective_group": None,
                "credits": None,
                "source_scheme": "UIT-RGPV (Autonomous) MCA Curriculum",
                "effective_date": "2026-27",
                "verification_status": VerificationStatus.SYLLABUS_CONFIRMED,
                "verification_notes": "Practical laboratory course.",
            },
        ],
    },
    {
        "semester_number": 3,
        "name": "Semester 3",
        "academic_focus": "Data Mining, AI, Departmental Electives & Minor Project",
        "courses": [
            {
                "id": "mca_sem3_dm",
                "name": "Data Mining",
                "code": "MCA301",
                "semester": 3,
                "course_type": McaCourseType.THEORY,
                "elective_group": None,
                "credits": 4,
                "source_scheme": "UIT-RGPV (Autonomous) MCA Curriculum",
                "effective_date": "2026-27",
                "verification_status": VerificationStatus.CONFIRMED,
                "verification_notes": "Course code and credits verified from official Semester 3 scheme.",
            },
            {
                "id": "mca_sem3_ai",
                "name": "Artificial Intelligence",
                "code": "MCA302",
                "semester": 3,
                "course_type": McaCourseType.THEORY,
                "elective_group": None,
                "credits": 4,
                "source_scheme": "UIT-RGPV (Autonomous) MCA Curriculum",
                "effective_date": "2026-27",
                "verification_status": VerificationStatus.CONFIRMED,
                "verification_notes": "Course code and credits verified from official Semester 3 scheme.",
            },
            {
                "id": "mca_sem3_elec1_python",
                "name": "Elective-I: Python Programming",
                "code": "MCA303",
                "semester": 3,
                "course_type": McaCourseType.ELECTIVE,
                "elective_group": "Elective-I",
                "credits": 4,
                "source_scheme": "UIT-RGPV (Autonomous) MCA Curriculum",
                "effective_date": "2026-27",
                "verification_status": VerificationStatus.CONFIRMED,
                "verification_notes": "Course code and credits verified from official Semester 3 scheme (Elective-I).",
            },
            {
                "id": "mca_sem3_elec2_mldl",
                "name": "Elective-II: Machine Learning and Deep Learning",
                "code": "MCA304",
                "semester": 3,
                "course_type": McaCourseType.ELECTIVE,
                "elective_group": "Elective-II",
                "credits": 4,
                "source_scheme": "UIT-RGPV (Autonomous) MCA Curriculum",
                "effective_date": "2026-27",
                "verification_status": VerificationStatus.CONFIRMED,
                "verification_notes": "Course code and credits verified from official Semester 3 scheme (Elective-II).",
            },
            {
                "id": "mca_sem3_elec3_ds",
                "name": "Elective-III: Distributed Systems",
                "code": "MCA305",
                "semester": 3,
                "course_type": McaCourseType.ELECTIVE,
                "elective_group": "Elective-III",
                "credits": 4,
                "source_scheme": "UIT-RGPV (Autonomous) MCA Curriculum",
                "effective_date": "2026-27",
                "verification_status": VerificationStatus.CONFIRMED,
                "verification_notes": "Course code and credits verified from official Semester 3 scheme (Elective-III).",
            },
            {
                "id": "mca_sem3_minor_proj",
                "name": "Minor Project",
                "code": "MCA306",
                "semester": 3,
                "course_type": McaCourseType.PROJECT,
                "elective_group": None,
                "credits": 8,
                "source_scheme": "UIT-RGPV (Autonomous) MCA Curriculum",
                "effective_date": "2026-27",
                "verification_status": VerificationStatus.CONFIRMED,
                "verification_notes": "Course code and credits verified from official Semester 3 scheme (Minor Project).",
            },
            {
                "id": "mca_sem3_elec1_lab",
                "name": "Elective-I Lab",
                "code": "MCA307",
                "semester": 3,
                "course_type": McaCourseType.LAB,
                "elective_group": "Elective-I",
                "credits": 4,
                "source_scheme": "UIT-RGPV (Autonomous) MCA Curriculum",
                "effective_date": "2026-27",
                "verification_status": VerificationStatus.CONFIRMED,
                "verification_notes": "Course code and credits verified from official Semester 3 scheme (Elective-I Lab).",
            },
        ],
    },
    {
        "semester_number": 4,
        "name": "Semester 4",
        "academic_focus": "Cloud, Blockchain, Advanced Computing & Enterprise Security",
        "courses": [
            {
                "id": "mca_sem4_cct",
                "name": "Cloud Computing Technologies",
                "code": None,
                "semester": 4,
                "course_type": McaCourseType.THEORY,
                "elective_group": None,
                "credits": None,
                "source_scheme": "UIT-RGPV (Autonomous) MCA Curriculum",
                "effective_date": "2026-27",
                "verification_status": VerificationStatus.SYLLABUS_CONFIRMED,
                "verification_notes": "Confirmed course name; code and credits pending examination scheme.",
            },
            {
                "id": "mca_sem4_crypto",
                "name": "Cryptocurrency and Blockchain Technologies",
                "code": None,
                "semester": 4,
                "course_type": McaCourseType.THEORY,
                "elective_group": None,
                "credits": None,
                "source_scheme": "UIT-RGPV (Autonomous) MCA Curriculum",
                "effective_date": "2026-27",
                "verification_status": VerificationStatus.SYLLABUS_CONFIRMED,
                "verification_notes": "Confirmed course name; code and credits pending examination scheme.",
            },
            {
                "id": "mca_sem4_adv_python",
                "name": "Advanced Python",
                "code": None,
                "semester": 4,
                "course_type": McaCourseType.THEORY,
                "elective_group": None,
                "credits": None,
                "source_scheme": "UIT-RGPV (Autonomous) MCA Curriculum",
                "effective_date": "2026-27",
                "verification_status": VerificationStatus.SYLLABUS_CONFIRMED,
                "verification_notes": "Confirmed course name; code and credits pending examination scheme.",
            },
            {
                "id": "mca_sem4_is",
                "name": "Information Security",
                "code": None,
                "semester": 4,
                "course_type": McaCourseType.THEORY,
                "elective_group": None,
                "credits": None,
                "source_scheme": "UIT-RGPV (Autonomous) MCA Curriculum",
                "effective_date": "2026-27",
                "verification_status": VerificationStatus.SYLLABUS_CONFIRMED,
                "verification_notes": "Confirmed course name; code and credits pending examination scheme.",
            },
            {
                "id": "mca_sem4_bda",
                "name": "Big Data Analytics",
                "code": None,
                "semester": 4,
                "course_type": McaCourseType.THEORY,
                "elective_group": None,
                "credits": None,
                "source_scheme": "UIT-RGPV (Autonomous) MCA Curriculum",
                "effective_date": "2026-27",
                "verification_status": VerificationStatus.SYLLABUS_CONFIRMED,
                "verification_notes": "Confirmed course name; code and credits pending examination scheme.",
            },
        ],
    },
]


def get_mca_curriculum() -> McaCurriculumResponse:
    """
    Constructs and returns the complete, validated MCA curriculum schema response.
    """
    semester_models: List[McaSemesterMetadata] = []
    for sem in MCA_SEMESTERS_DATA:
        course_models = [McaCourseMetadata(**c) for c in sem["courses"]]
        semester_models.append(
            McaSemesterMetadata(
                semester_number=sem["semester_number"],
                name=sem["name"],
                academic_focus=sem.get("academic_focus"),
                total_courses=len(course_models),
                courses=course_models,
            )
        )

    return McaCurriculumResponse(
        program_name=MCA_PROGRAM_METADATA["program_name"],
        program_code=MCA_PROGRAM_METADATA["program_code"],
        institution=MCA_PROGRAM_METADATA["institution"],
        department=MCA_PROGRAM_METADATA["department"],
        total_semesters=MCA_PROGRAM_METADATA["total_semesters"],
        total_courses=MCA_PROGRAM_METADATA["total_courses"],
        semesters=semester_models,
    )


def get_all_mca_courses() -> List[McaCourseMetadata]:
    """
    Returns a flat list of all 26 confirmed MCA course models.
    """
    curriculum = get_mca_curriculum()
    courses: List[McaCourseMetadata] = []
    for sem in curriculum.semesters:
        courses.extend(sem.courses)
    return courses


def get_mca_courses_by_semester(semester_number: int) -> List[McaCourseMetadata]:
    """
    Returns courses associated with a given semester (1 to 4).
    """
    curriculum = get_mca_curriculum()
    for sem in curriculum.semesters:
        if sem.semester_number == semester_number:
            return sem.courses
    return []


def get_mca_course_by_id(course_id: str) -> Optional[McaCourseMetadata]:
    """
    Lookup a course by its unique identifier.
    """
    for course in get_all_mca_courses():
        if course.id == course_id:
            return course
    return None


def get_mca_semester(semester_number: int) -> Optional[McaSemesterMetadata]:
    """
    Returns the McaSemesterMetadata for a given semester number (1 to 4),
    or None if the semester does not exist.
    """
    curriculum = get_mca_curriculum()
    for sem in curriculum.semesters:
        if sem.semester_number == semester_number:
            return sem
    return None


def get_mca_electives_by_semester(semester_number: int) -> List[McaCourseMetadata]:
    """
    Returns elective courses for a given semester.
    """
    return [
        c for c in get_mca_courses_by_semester(semester_number)
        if c.course_type == McaCourseType.ELECTIVE
    ]

