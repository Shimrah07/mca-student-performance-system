"""
backend/tests/test_database.py

Automated tests for Stage 3: Backend Database Integration.

Tests cover:
1. Configuration loading, dynamic URL construction, special character encoding, and credential masking.
2. ORM models (Student, PredictionRecord): instantiation, required fields, defaults, JSON serialization.
3. Relational integrity: 1-to-N Student-to-Predictions relationship, cascade behavior, and standalone predictions.
4. Session lifecycle: transaction commit, rollback, and generator cleanup in get_db().
5. Database initialization (init_db): idempotency and non-destructive table creation.
6. Connection verification (check_db_connection): success, error handling, and password sanitization.
7. Database health endpoint: GET /health/db.

All database tests use an isolated in-memory SQLite database (`sqlite:///:memory:`)
so they run independently and do NOT require a live MySQL server.
"""

import os
import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from fastapi.testclient import TestClient

from app.config import Settings
from app.database import Base, get_engine, init_db, check_db_connection, get_db
from app.models.student import Student
from app.models.prediction import PredictionRecord
from app.main import app

# Test client for FastAPI routes
client = TestClient(app)


# ---------------------------------------------------------------------------
# Fixtures for Isolated Database Testing
# ---------------------------------------------------------------------------
@pytest.fixture
def in_memory_engine():
    """Create an isolated in-memory SQLite database engine for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    init_db(target_engine=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def db_session(in_memory_engine):
    """Provide a clean transactional session bound to the in-memory engine."""
    Session = sessionmaker(autocommit=False, autoflush=False, bind=in_memory_engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


# ---------------------------------------------------------------------------
# 1. Configuration Tests
# ---------------------------------------------------------------------------
class TestDatabaseConfiguration:
    def test_default_settings(self, monkeypatch):
        """Verify default configuration attributes when environment variables are not set."""
        monkeypatch.delenv("DB_HOST", raising=False)
        monkeypatch.delenv("DB_PORT", raising=False)
        monkeypatch.delenv("DB_NAME", raising=False)
        monkeypatch.delenv("DB_USER", raising=False)
        monkeypatch.delenv("DB_PASSWORD", raising=False)
        monkeypatch.delenv("APP_ENV", raising=False)
        monkeypatch.delenv("DATABASE_URL", raising=False)

        cfg = Settings()
        assert cfg.db_host in ("localhost", "127.0.0.1")
        assert cfg.db_port == 3306
        assert cfg.db_name == "student_performance_db"
        assert cfg.db_user == "root"
        assert cfg.app_env in ("development", "testing", "production")

    def test_database_url_construction(self, monkeypatch):
        """Verify dynamic URL construction using PyMySQL driver."""
        monkeypatch.setenv("DB_HOST", "db.example.com")
        monkeypatch.setenv("DB_PORT", "3307")
        monkeypatch.setenv("DB_NAME", "test_db")
        monkeypatch.setenv("DB_USER", "admin")
        monkeypatch.setenv("DB_PASSWORD", "secret123")
        monkeypatch.delenv("DATABASE_URL", raising=False)

        cfg = Settings()
        expected = "mysql+pymysql://admin:secret123@db.example.com:3307/test_db"
        assert cfg.database_url == expected

    def test_database_url_special_characters(self, monkeypatch):
        """Verify that special characters in passwords/usernames are URL-encoded."""
        monkeypatch.setenv("DB_HOST", "localhost")
        monkeypatch.setenv("DB_PORT", "3306")
        monkeypatch.setenv("DB_NAME", "db_name")
        monkeypatch.setenv("DB_USER", "user@domain")
        monkeypatch.setenv("DB_PASSWORD", "p@ss:w/ord#1")
        monkeypatch.delenv("DATABASE_URL", raising=False)

        cfg = Settings()
        # '@' becomes '%40', ':' becomes '%3A', '/' becomes '%2F', '#' becomes '%23'
        assert "user%40domain:p%40ss%3Aw%2Ford%231@" in cfg.database_url

    def test_safe_database_url_masks_password(self, monkeypatch):
        """Verify safe_database_url never exposes the raw password."""
        monkeypatch.setenv("DB_HOST", "mysql-host.internal")
        monkeypatch.setenv("DB_PORT", "3306")
        monkeypatch.setenv("DB_NAME", "student_db")
        monkeypatch.setenv("DB_USER", "app_user")
        monkeypatch.setenv("DB_PASSWORD", "super_secret_pw")
        monkeypatch.delenv("DATABASE_URL", raising=False)

        cfg = Settings()
        safe_url = cfg.safe_database_url
        assert "super_secret_pw" not in safe_url
        assert "app_user:***@mysql-host.internal:3306/student_db" in safe_url

    def test_database_url_env_override(self, monkeypatch):
        """Verify explicit DATABASE_URL environment variable takes precedence."""
        custom_url = "sqlite:///./custom_test.db"
        monkeypatch.setenv("DATABASE_URL", custom_url)

        cfg = Settings()
        assert cfg.database_url == custom_url

    def test_invalid_db_port_fallback(self, monkeypatch):
        """Verify invalid non-numeric DB_PORT safely falls back to default 3306."""
        monkeypatch.setenv("DB_PORT", "not_a_number")
        cfg = Settings()
        assert cfg.db_port == 3306


# ---------------------------------------------------------------------------
# 2. ORM Models Tests (Student, PredictionRecord)
# ---------------------------------------------------------------------------
class TestORMModels:
    def test_create_student_success(self, db_session):
        """Verify Student creation with anonymized code and auto-timestamps."""
        student = Student(student_code="STU-001")
        db_session.add(student)
        db_session.commit()
        db_session.refresh(student)

        assert student.id is not None
        assert student.student_code == "STU-001"
        assert isinstance(student.created_at, datetime)
        assert isinstance(student.updated_at, datetime)
        assert "<Student(id=" in repr(student)

        # Verify to_dict output
        d = student.to_dict()
        assert d["id"] == student.id
        assert d["student_code"] == "STU-001"
        assert "created_at" in d
        assert "updated_at" in d

    def test_student_code_unique_constraint(self, db_session):
        """Verify duplicate student_code raises an IntegrityError."""
        student1 = Student(student_code="STU-DUPLICATE")
        student2 = Student(student_code="STU-DUPLICATE")

        db_session.add(student1)
        db_session.commit()

        db_session.add(student2)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_create_prediction_record_all_fields(self, db_session):
        """Verify PredictionRecord creation with structured JSON fields."""
        features = {
            "school": "GP",
            "sex": "F",
            "age": 16,
            "studytime": 3,
            "failures": 0,
            "absences": 4,
        }
        probs = {
            "Needs Improvement": 0.05,
            "Average": 0.20,
            "Good": 0.55,
            "Excellent": 0.20,
        }
        weak_areas = ["studytime"]
        recs = {
            "summary": "Overall good trajectory; maintain consistent study habits.",
            "actionable_recommendations": [
                {
                    "priority": "Medium",
                    "category": "Study Habits",
                    "action": "Maintain 5 to 10 hours per week of structured revision.",
                }
            ],
            "strengths": ["Zero past course failures indicates solid fundamentals."],
            "disclaimer": "Indicative guidance only; not an exam guarantee.",
        }

        record = PredictionRecord(
            subject="Mathematics",
            scenario="Scenario A",
            model_name="student_mat_scenario_a_logistic_regression",
            model_version="1.0.0",
            predicted_category="Good",
            prediction_probabilities=probs,
            input_features=features,
            weak_areas=weak_areas,
            recommendations=recs,
        )
        db_session.add(record)
        db_session.commit()
        db_session.refresh(record)

        assert record.id is not None
        assert record.student_id is None  # Standalone anonymous prediction
        assert record.subject == "Mathematics"
        assert record.scenario == "Scenario A"
        assert record.model_name == "student_mat_scenario_a_logistic_regression"
        assert record.model_version == "1.0.0"
        assert record.predicted_category == "Good"
        assert record.input_features["school"] == "GP"
        assert record.input_features["age"] == 16
        assert record.prediction_probabilities["Good"] == 0.55
        assert record.weak_areas == ["studytime"]
        assert record.recommendations["summary"].startswith("Overall good")
        assert isinstance(record.created_at, datetime)
        assert "<PredictionRecord(id=" in repr(record)

        # Verify to_dict output
        d = record.to_dict()
        assert d["id"] == record.id
        assert d["subject"] == "Mathematics"
        assert d["predicted_category"] == "Good"
        assert d["input_features"] == features
        assert d["recommendations"] == recs

    def test_prediction_record_required_fields(self, db_session):
        """Verify that omitting required fields (e.g. subject, predicted_category) fails."""
        # Missing required fields
        invalid_record = PredictionRecord(
            model_name="model_v1",
            # missing subject, scenario, predicted_category, input_features
        )
        db_session.add(invalid_record)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_student_prediction_relationship(self, db_session):
        """Verify 1-to-N relationship and cascade delete behavior."""
        student = Student(student_code="STU-RELATION")
        db_session.add(student)
        db_session.commit()
        db_session.refresh(student)

        pred1 = PredictionRecord(
            student_id=student.id,
            subject="Mathematics",
            scenario="Scenario A",
            model_name="lr_model",
            predicted_category="Average",
            input_features={"studytime": 2},
        )
        pred2 = PredictionRecord(
            student_id=student.id,
            subject="Portuguese",
            scenario="Scenario B",
            model_name="rf_model",
            predicted_category="Good",
            input_features={"studytime": 2, "G1": 14},
        )
        db_session.add_all([pred1, pred2])
        db_session.commit()
        db_session.refresh(student)

        assert len(student.predictions) == 2
        categories = {p.predicted_category for p in student.predictions}
        assert categories == {"Average", "Good"}

        # Delete student -> cascade delete should remove associated predictions
        db_session.delete(student)
        db_session.commit()

        remaining = db_session.query(PredictionRecord).filter(
            PredictionRecord.student_id == student.id
        ).all()
        assert len(remaining) == 0


# ---------------------------------------------------------------------------
# 3. Session Lifecycle & Engine Tests
# ---------------------------------------------------------------------------
class TestSessionLifecycle:
    def test_get_engine_sqlite(self):
        """Verify get_engine properly configures SQLite engines."""
        eng = get_engine("sqlite:///:memory:")
        assert eng.name == "sqlite"
        eng.dispose()

    def test_get_db_generator(self, in_memory_engine, monkeypatch):
        """Verify get_db() yields a valid session and closes it on generator exit."""
        TestSessionLocal = sessionmaker(bind=in_memory_engine)
        monkeypatch.setattr("app.database.SessionLocal", TestSessionLocal)

        gen = get_db()
        session = next(gen)
        from sqlalchemy.orm import Session
        assert isinstance(session, Session)

        # Execute a quick query to verify session is active
        res = session.execute(text("SELECT 1")).scalar()
        assert res == 1

        # Closing generator should trigger `finally: db.close()`
        with pytest.raises(StopIteration):
            next(gen)

    def test_init_db_idempotency(self, in_memory_engine):
        """Verify init_db can be called repeatedly without dropping or erroring."""
        # Calling init_db twice should be completely safe
        init_db(target_engine=in_memory_engine)
        init_db(target_engine=in_memory_engine)

        inspector = inspect(in_memory_engine)
        tables = set(inspector.get_table_names())
        assert "students" in tables
        assert "prediction_records" in tables

    def test_init_db_mca_only_creates_exactly_13_tables(self):
        """Verify init_db(mca_only=True) creates strictly the 13 approved MCA tables."""
        from app.database import MCA_TABLE_ALLOWLIST
        eng = create_engine("sqlite:///:memory:")
        init_db(target_engine=eng, mca_only=True)

        inspector = inspect(eng)
        created_tables = set(inspector.get_table_names())

        assert len(created_tables) == 13
        assert created_tables == set(MCA_TABLE_ALLOWLIST)
        assert "students" not in created_tables
        assert "prediction_records" not in created_tables

        # Verify all 19 foreign keys are present in SQLite metadata
        total_fks = 0
        for tbl in created_tables:
            fks = inspector.get_foreign_keys(tbl)
            total_fks += len(fks)
        assert total_fks == 19

        eng.dispose()

    def test_init_db_mca_only_idempotency(self):
        """Verify init_db(mca_only=True) can be called repeatedly without dropping or erroring."""
        eng = create_engine("sqlite:///:memory:")
        init_db(target_engine=eng, mca_only=True)
        init_db(target_engine=eng, mca_only=True)

        inspector = inspect(eng)
        assert len(inspector.get_table_names()) == 13
        eng.dispose()


# ---------------------------------------------------------------------------
# 4. Connection Verification & Credential Masking Tests
# ---------------------------------------------------------------------------
class TestConnectionVerification:
    def test_check_db_connection_success(self, in_memory_engine):
        """Verify check_db_connection reports success for reachable engine."""
        ok, msg = check_db_connection(target_engine=in_memory_engine)
        assert ok is True
        assert "Database connection successful" in msg

    def test_check_db_connection_failure_masks_password(self, monkeypatch):
        """Verify failure message does not leak database password."""
        monkeypatch.setattr("app.config.settings.db_password", "super_secret_pass_123")

        # Create an engine pointing to an unreachable port / invalid host
        bad_engine = create_engine(
            "mysql+pymysql://root:super_secret_pass_123@127.0.0.1:54321/nonexistent_db",
            connect_args={"connect_timeout": 1},
        )

        ok, msg = check_db_connection(target_engine=bad_engine)
        assert ok is False
        assert "Database connection failed" in msg
        # Ensure raw password is NOT in the message
        assert "super_secret_pass_123" not in msg


# ---------------------------------------------------------------------------
# 5. Database Health API Endpoint Test
# ---------------------------------------------------------------------------
class TestDatabaseHealthEndpoint:
    def test_health_check_endpoint(self):
        """Verify existing GET /health endpoint is intact and unaffected."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["message"] == "API is running"
        assert "environment" in data

    def test_db_health_check_endpoint(self):
        """Verify GET /health/db returns connection status and masked URL."""
        response = client.get("/health/db")
        assert response.status_code == 200
        data = response.json()
        assert "database_connected" in data
        assert "message" in data
        assert "database_url" in data
        # Ensure password is not present in response URL
        assert "***" in data["database_url"] or ":" not in data["database_url"].split("@")[0]
