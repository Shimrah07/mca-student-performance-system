"""
backend/app/main.py

FastAPI application entry point.

Current state (Week V — Stage 1):
  - One endpoint: GET /health
  - CORS configured so the React frontend (localhost:5173) can call this API

Not yet implemented (will be added in later stages):
  - Database connection (SQLAlchemy)
  - Student record endpoints
  - ML prediction endpoint
  - Weak-area and recommendation logic
  - Authentication / roles

To run locally (from the backend/ directory, with venv activated):
    uvicorn app.main:app --reload

Then visit:
    http://localhost:8000/health   → health check
    http://localhost:8000/docs     → interactive API documentation (auto-generated)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

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
#
# What this does: allows the React frontend (running on a different port)
# to make HTTP requests to this API.  Without this, the browser would block
# those requests automatically.
#
# The allowed origins come from the .env file via settings.cors_origins.
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # e.g. ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],    # GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health", tags=["System"])
def health_check():
    """
    Health check endpoint.

    Returns a simple JSON response to confirm the API is running.
    This is the first thing to test after starting the server.

    Response example:
        {"status": "ok", "message": "API is running"}
    """
    return {
        "status": "ok",
        "message": "API is running",
        "environment": settings.app_env,
    }
