"""
backend/app/routers/__init__.py

Exports all API route definitions.
"""

from app.routers.predictions import router as predictions_router
from app.routers.mca_curriculum import router as mca_curriculum_router
from app.routers.mca_predictions import router as mca_predictions_router

__all__ = ["predictions_router", "mca_curriculum_router", "mca_predictions_router"]

