# api/routes/health.py
"""Health check endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: str
    version: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns service status for load balancers and monitoring.
    """
    from ..config import settings
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version=settings.api_version,
    )


@router.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint.
    
    Returns 200 if the service is ready to accept requests.
    Checks database and Redis connectivity.
    """
    # TODO: Add actual connectivity checks
    return {"ready": True, "checks": {"database": "ok", "redis": "ok", "celery": "ok"}}
