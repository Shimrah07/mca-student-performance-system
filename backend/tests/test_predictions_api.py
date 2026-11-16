"""
backend/tests/test_predictions_api.py

Automated tests for Stage 4: Prediction & Recommendation API Endpoints.

Test Coverage:
1. Valid predictions for all 4 candidate pipelines:
   - Mathematics, Scenario A (Logistic Regression, unweighted)
   - Mathematics, Scenario B (Decision Tree, unweighted)
   - Portuguese, Scenario A (Random Forest, balanced)
   - Portuguese, Scenario B (Decision Tree, balanced)
2. Strict data leakage prevention:
   - Rejection of G2 (period 2 grade) in input payload.
   - Rejection of G3 (final exam grade) in input payload.
3. Scenario validation:
   - Scenario A succeeds without G1.
   - Scenario B requires G1 and fails with 422 if G1 is omitted.
4. Input validation:
   - Invalid categorical choices (e.g., school='INVALID').
   - Out-of-bounds numerical ranges (e.g., age=35, studytime=10).
   - Invalid subject or scenario enums.
5. Probabilities & recommendations:
   - Uncalibrated probability dictionary structure and disclaimer note.
   - Rule-based recommendations payload (summary, actions, strengths, disclaimer).
6. Persistence handling:
   - Successful database persistence with linked student_code.
   - Retrieval via GET /api/predictions/{id}.
   - 404 Not Found for nonexistent prediction ID.
   - Pagination via GET /api/predictions.
   - Graceful fallback (HTTP 200 with persisted=False) when database is unavailable.
"""

import pytest
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database import Base, get_db, init_db
from app.main import app
from app.services.prediction_service import clear_model_cache

client = TestClient(app)


# ---------------------------------------------------------------------------
# Test Fixtures & Base Payload
# ---------------------------------------------------------------------------
@pytest.fixture
def in_memory_db():
    """Create an isolated in-memory SQLite database and override get_db."""
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    init_db(target_engine=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield test_engine
    app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


@pytest.fixture
def base_features():
    """Standard valid feature dictionary for Scenario A (30 features)."""
    return {
        "school": "GP",
        "sex": "F",
        "address": "U",
        "famsize": "GT3",
        "Pstatus": "T",
        "schoolsup": "yes",
        "famsup": "no",
        "paid": "no",
        "activities": "yes",
        "nursery": "yes",
        "higher": "yes",
        "internet": "yes",
        "romantic": "no",
        "Mjob": "other",
        "Fjob": "services",
        "reason": "course",
        "guardian": "mother",
        "Medu": 3,
        "Fedu": 2,
        "traveltime": 1,
        "studytime": 3,
        "failures": 0,
        "famrel": 4,
        "freetime": 3,
        "goout": 2,
        "Dalc": 1,
        "Walc": 1,
        "health": 4,
        "age": 16,
        "absences": 4,
    }


# ---------------------------------------------------------------------------
# 1. Four Candidate Pipeline Predictions
# ---------------------------------------------------------------------------
class TestCandidatePipelinePredictions:
    def test_predict_mathematics_scenario_a(self, in_memory_db, base_features):
        """Mathematics, Scenario A: Logistic Regression (unweighted)."""
        payload = {
            "subject": "Mathematics",
            "scenario": "Scenario A",
            "features": base_features,
            "student_code": "STU-MAT-A",
        }
        response = client.post("/api/predictions", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["subject"] == "Mathematics"
        assert data["scenario"] == "Scenario A"
        assert "Logistic Regression" in data["model_name"]
        assert data["predicted_category"] in ("Needs Improvement", "Average", "Good", "Excellent")
        assert data["prediction_probabilities"] is not None
        assert "Average" in data["prediction_probabilities"]
        assert "Indicative model estimates only" in data["probabilities_note"]
        assert len(data["actionable_recommendations"]) > 0
        assert data["persisted"] is True
        assert data["prediction_id"] is not None

    def test_predict_mathematics_scenario_b(self, in_memory_db, base_features):
        """Mathematics, Scenario B: Decision Tree (unweighted)."""
        features_b = dict(base_features)
        features_b["G1"] = 15  # Good first-period mark

        payload = {
            "subject": "Mathematics",
            "scenario": "Scenario B",
            "features": features_b,
            "student_code": "STU-MAT-B",
        }
        response = client.post("/api/predictions", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["subject"] == "Mathematics"
        assert data["scenario"] == "Scenario B"
        assert "Decision Tree" in data["model_name"]
        assert data["predicted_category"] in ("Needs Improvement", "Average", "Good", "Excellent")
        assert data["persisted"] is True
        assert data["prediction_id"] is not None

    def test_predict_portuguese_scenario_a(self, in_memory_db, base_features):
        """Portuguese, Scenario A: Random Forest (balanced)."""
        payload = {
            "subject": "Portuguese",
            "scenario": "Scenario A",
            "features": base_features,
            "student_code": "STU-POR-A",
        }
        response = client.post("/api/predictions", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["subject"] == "Portuguese"
        assert data["scenario"] == "Scenario A"
        assert "Random Forest" in data["model_name"]
        assert data["predicted_category"] in ("Needs Improvement", "Average", "Good", "Excellent")
        assert data["persisted"] is True

    def test_predict_portuguese_scenario_b(self, in_memory_db, base_features):
        """Portuguese, Scenario B: Decision Tree (balanced)."""
        features_b = dict(base_features)
        features_b["G1"] = 11

        payload = {
            "subject": "Portuguese",
            "scenario": "Scenario B",
            "features": features_b,
            "student_code": "STU-POR-B",
        }
        response = client.post("/api/predictions", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["subject"] == "Portuguese"
        assert data["scenario"] == "Scenario B"
        assert "Decision Tree" in data["model_name"]
        assert data["predicted_category"] in ("Needs Improvement", "Average", "Good", "Excellent")
        assert data["persisted"] is True


# ---------------------------------------------------------------------------
# 2. Data Leakage Prevention Tests (Rejecting G2 and G3)
# ---------------------------------------------------------------------------
class TestDataLeakageRejection:
    def test_reject_g2_in_scenario_a(self, in_memory_db, base_features):
        """Attempting to supply G2 in Scenario A must be strictly rejected (422)."""
        features_leak = dict(base_features)
        features_leak["G2"] = 14

        payload = {
            "subject": "Mathematics",
            "scenario": "Scenario A",
            "features": features_leak,
        }
        response = client.post("/api/predictions", json=payload)
        assert response.status_code == 422
        assert "Data leakage detected" in response.text
        assert "G2" in response.text

    def test_reject_g3_in_scenario_b(self, in_memory_db, base_features):
        """Attempting to supply G3 in Scenario B must be strictly rejected (422)."""
        features_leak = dict(base_features)
        features_leak["G1"] = 12
        features_leak["G3"] = 15

        payload = {
            "subject": "Portuguese",
            "scenario": "Scenario B",
            "features": features_leak,
        }
        response = client.post("/api/predictions", json=payload)
        assert response.status_code == 422
        assert "Data leakage detected" in response.text
        assert "G3" in response.text


# ---------------------------------------------------------------------------
# 3. Scenario Requirements & Input Validation Tests
# ---------------------------------------------------------------------------
class TestScenarioAndInputValidation:
    def test_scenario_b_missing_g1_fails(self, in_memory_db, base_features):
        """Scenario B without G1 must raise 422 Unprocessable Entity."""
        payload = {
            "subject": "Mathematics",
            "scenario": "Scenario B",
            "features": base_features,  # Missing G1
        }
        response = client.post("/api/predictions", json=payload)
        assert response.status_code == 422
        assert "Scenario B (Mid-Term) requires 'G1'" in response.text

    def test_scenario_a_ignores_or_allows_omitted_g1(self, in_memory_db, base_features):
        """Scenario A without G1 must succeed cleanly."""
        assert "G1" not in base_features
        payload = {
            "subject": "Mathematics",
            "scenario": "Scenario A",
            "features": base_features,
        }
        response = client.post("/api/predictions", json=payload)
        assert response.status_code == 200

    def test_invalid_categorical_field_fails(self, in_memory_db, base_features):
        """Invalid category option (e.g. school='INVALID') must fail with 422."""
        invalid_features = dict(base_features)
        invalid_features["school"] = "INVALID"

        payload = {
            "subject": "Mathematics",
            "scenario": "Scenario A",
            "features": invalid_features,
        }
        response = client.post("/api/predictions", json=payload)
        assert response.status_code == 422

    def test_out_of_bounds_numerical_field_fails(self, in_memory_db, base_features):
        """Out of bounds value (e.g. Medu=10 or studytime=9) must fail with 422."""
        invalid_features = dict(base_features)
        invalid_features["studytime"] = 9  # Allowed is 1 to 4

        payload = {
            "subject": "Mathematics",
            "scenario": "Scenario A",
            "features": invalid_features,
        }
        response = client.post("/api/predictions", json=payload)
        assert response.status_code == 422

    def test_invalid_subject_fails(self, in_memory_db, base_features):
        """Unsupported subject must fail with 422."""
        payload = {
            "subject": "Science",
            "scenario": "Scenario A",
            "features": base_features,
        }
        response = client.post("/api/predictions", json=payload)
        assert response.status_code == 422

    def test_invalid_scenario_fails(self, in_memory_db, base_features):
        """Unsupported scenario must fail with 422."""
        payload = {
            "subject": "Mathematics",
            "scenario": "Scenario C",
            "features": base_features,
        }
        response = client.post("/api/predictions", json=payload)
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# 4. Persistence & Retrieval Lifecycle Tests
# ---------------------------------------------------------------------------
class TestPersistenceAndRetrieval:
    def test_prediction_retrieval_by_id(self, in_memory_db, base_features):
        """Retrieve a saved prediction by ID via GET /api/predictions/{id}."""
        # 1. Post a prediction
        payload = {
            "subject": "Mathematics",
            "scenario": "Scenario A",
            "features": base_features,
            "student_code": "STU-RETRIEVE",
        }
        post_resp = client.post("/api/predictions", json=payload)
        assert post_resp.status_code == 200
        pred_id = post_resp.json()["prediction_id"]
        assert pred_id is not None

        # 2. Retrieve prediction
        get_resp = client.get(f"/api/predictions/{pred_id}")
        assert get_resp.status_code == 200
        data = get_resp.json()

        assert data["id"] == pred_id
        assert data["subject"] == "Mathematics"
        assert data["scenario"] == "Scenario A"
        assert data["predicted_category"] == post_resp.json()["predicted_category"]
        assert data["input_features"]["school"] == "GP"
        assert data["recommendations"]["summary"] is not None

    def test_get_nonexistent_prediction_404(self, in_memory_db):
        """Querying a nonexistent prediction ID returns 404."""
        response = client.get("/api/predictions/999999")
        assert response.status_code == 404
        assert "not found" in response.text.lower()

    def test_list_predictions_pagination(self, in_memory_db, base_features):
        """Test GET /api/predictions pagination with limit and offset."""
        # Create 3 predictions
        for i in range(3):
            features = dict(base_features)
            features["absences"] = i * 2
            client.post(
                "/api/predictions",
                json={
                    "subject": "Mathematics",
                    "scenario": "Scenario A",
                    "features": features,
                    "student_code": f"STU-PAGINATION-{i}",
                },
            )

        # List records
        list_resp = client.get("/api/predictions?limit=2&offset=0")
        assert list_resp.status_code == 200
        data = list_resp.json()
        assert data["total"] >= 3
        assert len(data["items"]) == 2

    def test_guest_prediction_persisted_without_student_code(self, in_memory_db, base_features):
        """Prediction without student_code succeeds and is saved as anonymous record."""
        payload = {
            "subject": "Portuguese",
            "scenario": "Scenario A",
            "features": base_features,
            # No student_code supplied
        }
        resp = client.post("/api/predictions", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["persisted"] is True
        assert data["prediction_id"] is not None

        # Verify student_id is null on the record
        record_resp = client.get(f"/api/predictions/{data['prediction_id']}")
        assert record_resp.json()["student_id"] is None

    def test_graceful_degradation_when_database_fails(self, base_features, monkeypatch):
        """
        If the database throws an error or is unreachable during persistence,
        the prediction must still succeed (HTTP 200) with persisted=False and prediction_id=None.
        """
        # Override get_db to simulate database session failure on commit
        from unittest.mock import MagicMock
        mock_session = MagicMock()
        mock_session.commit.side_effect = RuntimeError("Simulated DB connection failure")

        def broken_get_db():
            yield mock_session

        app.dependency_overrides[get_db] = broken_get_db
        try:
            payload = {
                "subject": "Mathematics",
                "scenario": "Scenario A",
                "features": base_features,
            }
            resp = client.post("/api/predictions", json=payload)
            assert resp.status_code == 200
            data = resp.json()
            assert data["persisted"] is False
            assert data["prediction_id"] is None
            assert data["predicted_category"] in ("Needs Improvement", "Average", "Good", "Excellent")
            assert len(data["actionable_recommendations"]) > 0
        finally:
            app.dependency_overrides.pop(get_db, None)
