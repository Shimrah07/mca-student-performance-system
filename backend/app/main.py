"""
backend/app/main.py

FastAPI application entry point.

Current state:
  - System health check: GET /health
  - Database connectivity check: GET /health/db
  - Prediction & recommendation endpoints: POST /api/predictions, GET /api/predictions/{id}, GET /api/predictions
  - CORS configured for React frontend (localhost:5173 by default)
  - Database integration configured (SQLAlchemy ORM + PyMySQL)

To run locally (from the backend/ directory, with venv activated):
    uvicorn app.main:app --reload

Interactive API documentation:
    http://localhost:8000/docs
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path so ml/ can be imported regardless of execution directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import check_db_connection
from app.routers import (
    mca_curriculum_router,
    mca_predictions_router,
    predictions_router,
)

# ---------------------------------------------------------------------------
# Create the FastAPI application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="AI-Based Student Performance Prediction & Academic Support System",
    description=(
        "A FastAPI backend for predicting student performance categories "
        "(Excellent / Good / Average / Needs Improvement), identifying weak "
        "academic areas, and providing supportive recommendations. "
        "MCA 3rd Semester Minor Project — UIT-RGPV (Autonomous), Bhopal."
    ),
    version="0.1.0",
)

# ---------------------------------------------------------------------------
# CORS — Cross-Origin Resource Sharing
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(predictions_router, prefix="/api")
app.include_router(mca_curriculum_router, prefix="/api/mca")
app.include_router(mca_predictions_router, prefix="/api/mca")



# ---------------------------------------------------------------------------
# System Routes
# ---------------------------------------------------------------------------

@app.get("/health", tags=["System"])
def health_check():
    """
    Health check endpoint.

    Returns a simple JSON response to confirm the API is running.
    Response example:
        {"status": "ok", "message": "API is running", "environment": "development"}
    """
    return {
        "status": "ok",
        "message": "API is running",
        "environment": settings.app_env,
    }


@app.get("/health/db", tags=["System"])
def database_health_check():
    """
    Database connectivity check endpoint.

    Verifies whether the database engine can successfully connect and execute
    a simple query. Never leaks passwords or private credentials.
    """
    connected, message = check_db_connection()
    return {
        "database_connected": connected,
        "message": message,
        "database_url": settings.safe_database_url,
    }
