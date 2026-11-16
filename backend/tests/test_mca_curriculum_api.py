"""
backend/tests/test_mca_curriculum_api.py

Automated integration tests for Phase 2A: MCA Curriculum Read-Only API.

Verifies:
1. Successful retrieval of all four semesters via GET /api/mca/curriculum.
2. Exactly 26 courses represented in the complete curriculum.
3. Correct Semester 3 elective associations (Elective-I, II, III, Elective-I Lab, Minor Project).
4. Successful retrieval of each individual semester via GET /api/mca/semesters/{n}.
5. Safe handling and rejection of invalid/nonexistent semester numbers (0, 5, 99, -1, non-numeric).
6. Response schema validation adhering strictly to McaCurriculumResponse and McaSemesterMetadata.
7. Legacy UCI prediction and health endpoints remain operational without regression.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.mca import (
    McaCurriculumResponse,
    McaSemesterMetadata,
)

client = TestClient(app)


# ===========================================================================
# 1. Complete Curriculum Endpoint (GET /api/mca/curriculum)
# ===========================================================================

def test_get_mca_curriculum_success():
    """
    Test GET /api/mca/curriculum returns HTTP 200 and all four semesters.
    """
    response = client.get("/api/mca/curriculum")
    assert response.status_code == 200

    data = response.json()
    assert data["program_name"] == "Master of Computer Applications"
    assert data["program_code"] == "MCA"
    assert "UIT-RGPV" in data["institution"] or "University Institute of Technology" in data["institution"]
    assert data["total_semesters"] == 4
    assert data["total_courses"] == 26
    assert len(data["semesters"]) == 4

    semester_numbers = [sem["semester_number"] for sem in data["semesters"]]
    assert semester_numbers == [1, 2, 3, 4]


def test_complete_curriculum_contains_exactly_26_courses():
    """
    Verify the curriculum response contains exactly 26 courses with
    verified counts per semester: Sem 1 (7), Sem 2 (7), Sem 3 (7), Sem 4 (5).
    """
    response = client.get("/api/mca/curriculum")
    assert response.status_code == 200

    data = response.json()
    semesters = data["semesters"]

    assert len(semesters[0]["courses"]) == 7  # Sem 1
    assert len(semesters[1]["courses"]) == 7  # Sem 2
    assert len(semesters[2]["courses"]) == 7  # Sem 3
    assert len(semesters[3]["courses"]) == 5  # Sem 4

    all_courses = [course for sem in semesters for course in sem["courses"]]
    assert len(all_courses) == 26

    # Verify uniqueness of course IDs
    course_ids = [c["id"] for c in all_courses]
    assert len(course_ids) == len(set(course_ids)), "Every course must have a unique ID"

    # Verify verified course codes and credits for Semesters 1 and 3
    sem1_courses = semesters[0]["courses"]
    sem1_expected = {
        "mca_sem1_os": ("MCA108", 4),
        "mca_sem1_c_prog": ("MCA109", 4),
        "mca_sem1_math": ("MCA110", 4),
        "mca_sem1_fct": ("MCA111", 4),
        "mca_sem1_tc": ("MCA112", 4),
        "mca_sem1_c_lab": ("MCA113", 8),
        "mca_sem1_os_lab": ("MCA114", 4),
    }
    for c in sem1_courses:
        expected_code, expected_credits = sem1_expected[c["id"]]
        assert c["code"] == expected_code
        assert c["credits"] == expected_credits
        assert c["verification_status"] == "confirmed"

    sem3_courses = semesters[2]["courses"]
    sem3_expected = {
        "mca_sem3_dm": ("MCA301", 4),
        "mca_sem3_ai": ("MCA302", 4),
        "mca_sem3_elec1_python": ("MCA303", 4),
        "mca_sem3_elec2_mldl": ("MCA304", 4),
        "mca_sem3_elec3_ds": ("MCA305", 4),
        "mca_sem3_minor_proj": ("MCA306", 8),
        "mca_sem3_elec1_lab": ("MCA307", 4),
    }
    for c in sem3_courses:
        expected_code, expected_credits = sem3_expected[c["id"]]
        assert c["code"] == expected_code
        assert c["credits"] == expected_credits
        assert c["verification_status"] == "confirmed"

    # Verify that unverified course codes and credits in Semesters 2 and 4 remain safely null
    sem2_and_4_courses = semesters[1]["courses"] + semesters[3]["courses"]
    for course in sem2_and_4_courses:
        assert course["code"] is None
        assert course["credits"] is None
        assert course["verification_status"] == "syllabus_confirmed_code_pending"
        assert course["source_scheme"] == "UIT-RGPV (Autonomous) MCA Curriculum"
        assert course["effective_date"] == "2026-27"


# ===========================================================================
# 2. Semester 3 Elective Associations
# ===========================================================================

def test_semester_3_elective_associations():
    """
    Verify confirmed elective tracks and project designations in Semester 3:
    - Elective-I = Python Programming (MCA303, 4 credits)
    - Elective-II = Machine Learning and Deep Learning (MCA304, 4 credits)
    - Elective-III = Distributed Systems (MCA305, 4 credits)
    - Elective-I Lab = Lab corresponding to Elective-I (MCA307, 4 credits)
    - Minor Project = Project archetype (MCA306, 8 credits)
    """
    response = client.get("/api/mca/semesters/3")
    assert response.status_code == 200

    sem3 = response.json()
    assert sem3["semester_number"] == 3
    assert sem3["total_courses"] == 7

    course_by_name = {c["name"]: c for c in sem3["courses"]}

    # Elective-I
    elec1 = course_by_name["Elective-I: Python Programming"]
    assert elec1["code"] == "MCA303"
    assert elec1["credits"] == 4
    assert elec1["course_type"] == "elective"
    assert elec1["elective_group"] == "Elective-I"
    assert elec1["verification_status"] == "confirmed"

    # Elective-II
    elec2 = course_by_name["Elective-II: Machine Learning and Deep Learning"]
    assert elec2["code"] == "MCA304"
    assert elec2["credits"] == 4
    assert elec2["course_type"] == "elective"
    assert elec2["elective_group"] == "Elective-II"
    assert elec2["verification_status"] == "confirmed"

    # Elective-III
    elec3 = course_by_name["Elective-III: Distributed Systems"]
    assert elec3["code"] == "MCA305"
    assert elec3["credits"] == 4
    assert elec3["course_type"] == "elective"
    assert elec3["elective_group"] == "Elective-III"
    assert elec3["verification_status"] == "confirmed"

    # Elective-I Lab
    elec1_lab = course_by_name["Elective-I Lab"]
    assert elec1_lab["code"] == "MCA307"
    assert elec1_lab["credits"] == 4
    assert elec1_lab["course_type"] == "lab"
    assert elec1_lab["elective_group"] == "Elective-I"
    assert elec1_lab["verification_status"] == "confirmed"

    # Minor Project
    minor_proj = course_by_name["Minor Project"]
    assert minor_proj["code"] == "MCA306"
    assert minor_proj["credits"] == 8
    assert minor_proj["course_type"] == "project"
    assert minor_proj["elective_group"] is None
    assert minor_proj["verification_status"] == "confirmed"



# ===========================================================================
# 3. Individual Semester Retrieval (GET /api/mca/semesters/{n})
# ===========================================================================

@pytest.mark.parametrize(
    "sem_num, expected_count, sample_course_name",
    [
        (1, 7, "Operating System"),
        (2, 7, "Database Management System"),
        (3, 7, "Artificial Intelligence"),
        (4, 5, "Cloud Computing Technologies"),
    ],
)
def test_get_individual_semesters_success(sem_num, expected_count, sample_course_name):
    """
    Verify successful retrieval for each individual semester 1 through 4.
    """
    response = client.get(f"/api/mca/semesters/{sem_num}")
    assert response.status_code == 200

    data = response.json()
    assert data["semester_number"] == sem_num
    assert data["name"] == f"Semester {sem_num}"
    assert data["total_courses"] == expected_count
    assert len(data["courses"]) == expected_count

    course_names = [c["name"] for c in data["courses"]]
    assert sample_course_name in course_names

    # Schema validation
    semester_obj = McaSemesterMetadata(**data)
    assert semester_obj.semester_number == sem_num


# ===========================================================================
# 4. Invalid Semester Handling
# ===========================================================================

@pytest.mark.parametrize("invalid_sem", [0, 5, -1, 99])
def test_get_semester_invalid_number_returns_404(invalid_sem):
    """
    Verify out-of-range semester numbers (0, 5, -1, 99) return HTTP 404.
    """
    response = client.get(f"/api/mca/semesters/{invalid_sem}")
    assert response.status_code == 404
    detail = response.json()["detail"]
    assert f"Semester {invalid_sem} not found" in detail
    assert "Valid MCA semesters are 1 through 4" in detail


def test_get_semester_non_integer_returns_422():
    """
    Verify non-integer semester parameter returns HTTP 422 Unprocessable Entity.
    """
    response = client.get("/api/mca/semesters/first_semester")
    assert response.status_code == 422


# ===========================================================================
# 5. Response Schema Validation
# ===========================================================================

def test_curriculum_response_matches_pydantic_schema():
    """
    Verify that the GET /api/mca/curriculum JSON strictly deserializes into McaCurriculumResponse.
    """
    response = client.get("/api/mca/curriculum")
    assert response.status_code == 200

    curriculum = McaCurriculumResponse(**response.json())
    assert curriculum.total_semesters == 4
    assert curriculum.total_courses == 26
    for sem in curriculum.semesters:
        assert isinstance(sem, McaSemesterMetadata)
        assert sem.semester_number in [1, 2, 3, 4]


# ===========================================================================
# 6. Legacy API Endpoints Verification (No Regression)
# ===========================================================================

def test_legacy_health_endpoints_remain_operational():
    """
    Verify existing /health and /health/db endpoints continue to work as expected.
    """
    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "ok"

    res_db = client.get("/health/db")
    assert res_db.status_code == 200
    assert "database_connected" in res_db.json()


def test_legacy_predictions_endpoints_remain_operational():
    """
    Verify existing POST /api/predictions and GET /api/predictions endpoints remain functional.
    """
    # 1. GET /api/predictions history
    res_history = client.get("/api/predictions")
    assert res_history.status_code == 200
    history_data = res_history.json()
    assert "total" in history_data
    assert "items" in history_data

    # 2. POST /api/predictions with valid benchmark sample
    sample_payload = {
        "subject": "Mathematics",
        "scenario": "Scenario A",
        "features": {
            "school": "GP",
            "sex": "F",
            "age": 17,
            "address": "U",
            "famsize": "GT3",
            "Pstatus": "T",
            "Medu": 3,
            "Fedu": 3,
            "Mjob": "other",
            "Fjob": "services",
            "reason": "course",
            "guardian": "mother",
            "traveltime": 1,
            "studytime": 3,
            "failures": 0,
            "schoolsup": "no",
            "famsup": "yes",
            "paid": "no",
            "activities": "yes",
            "nursery": "yes",
            "higher": "yes",
            "internet": "yes",
            "romantic": "no",
            "famrel": 4,
            "freetime": 3,
            "goout": 2,
            "Dalc": 1,
            "Walc": 1,
            "health": 4,
            "absences": 2,
        },
        "student_code": "REG-TEST-001",
    }
    res_pred = client.post("/api/predictions", json=sample_payload)
    assert res_pred.status_code == 200
    pred_data = res_pred.json()
    assert pred_data["predicted_category"] in ["Excellent", "Good", "Average", "Needs Improvement"]
    assert "actionable_recommendations" in pred_data
    assert "model_name" in pred_data
    assert "model_version" in pred_data

