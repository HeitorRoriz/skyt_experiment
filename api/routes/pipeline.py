# api/routes/pipeline.py
"""
Pipeline endpoints.

Submit and manage SKYT pipeline jobs.
Integrates with Supabase for persistence.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field

from .auth import get_current_user, User
from ..database import (
    get_jobs as db_get_jobs,
    get_job as db_get_job,
    create_job as db_create_job,
    update_job_status as db_update_job_status,
    get_contract as db_get_contract,
    check_runs_remaining,
    increment_runs,
)
from .contracts import get_template_contracts

# Try to import Celery task (optional - for async execution)
try:
    from workers.tasks import execute_skyt_job
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False


router = APIRouter(prefix="/pipeline")


# =============================================================================
# Request/Response Models
# =============================================================================

class ModelPins(BaseModel):
    """LLM model configuration."""
    model: str = Field(default="gpt-4o-mini", description="Model identifier")
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1, le=128000)
    seed: Optional[int] = Field(default=None, description="Random seed for reproducibility")


class PipelineRunRequest(BaseModel):
    """Request to run a SKYT pipeline job."""
    contract_id: str = Field(..., description="Contract identifier", example="fibonacci_basic")
    num_runs: int = Field(default=5, ge=1, le=100, description="Number of LLM generations")
    temperature: float = Field(default=0.0, ge=0.0, le=2.0, description="Sampling temperature")
    model: str = Field(default="gpt-4o-mini", description="LLM model to use")
    restriction_ids: List[UUID] = Field(default_factory=list, description="Restriction sets to apply")
    client_job_id: Optional[str] = Field(default=None, description="Client-provided job ID for idempotency")
    
    class Config:
        json_schema_extra = {
            "example": {
                "contract_id": "fibonacci_basic",
                "num_runs": 10,
                "temperature": 0.3,
                "model": "gpt-4o-mini",
                "restriction_ids": [],
            }
        }


class PipelineRunResponse(BaseModel):
    """Response after submitting a pipeline job."""
    job_id: UUID
    status: str
    message: str
    estimated_duration_seconds: Optional[int] = None


class JobSummary(BaseModel):
    """Brief job information for listings."""
    job_id: UUID
    contract_id: str
    status: str
    num_runs: int
    temperature: float
    created_at: datetime


# =============================================================================
# Job Helpers
# =============================================================================

# Keep mock jobs for backward compatibility during transition
_mock_jobs = {}


def get_user_contract_uuid(user_id: UUID, contract_id: str) -> Optional[UUID]:
    """Get user's contract UUID by contract_id, or check templates."""
    # First check user's contracts in database
    contract = db_get_contract(user_id, contract_id)
    if contract:
        return UUID(contract["id"])
    
    # Contract not in user's DB - they need to create it from template first
    return None


def get_job(user_id: UUID, job_id: UUID) -> Optional[dict]:
    """Get job by ID from database."""
    job = db_get_job(job_id)
    if job and str(job.get("user_id")) == str(user_id):
        return job
    return None


# =============================================================================
# Endpoints
# =============================================================================

@router.post("/run", response_model=PipelineRunResponse, status_code=status.HTTP_202_ACCEPTED)
async def run_pipeline(
    request: PipelineRunRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
):
    """
    Submit a new SKYT pipeline job.
    
    This endpoint queues a job for asynchronous execution. The job will:
    
    1. Load the specified contract
    2. Apply any restriction sets
    3. Generate `num_runs` outputs from the LLM
    4. Canonicalize outputs
    5. Compute repeatability metrics
    
    Use `GET /jobs/{job_id}` to check status and retrieve results.
    
    **Idempotency**: Provide `client_job_id` to prevent duplicate jobs on retries.
    If the same `client_job_id` is submitted twice, the existing job is returned.
    """
    # Check user quota
    if not check_runs_remaining(user.id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Monthly run limit reached ({user.runs_limit} runs). Upgrade your plan.",
        )
    
    # Validate contract exists (user's contract or template)
    contract_uuid = get_user_contract_uuid(user.id, request.contract_id)
    
    if not contract_uuid:
        # Check if it's a template - user needs to copy it first
        templates = get_template_contracts()
        if request.contract_id in templates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Contract '{request.contract_id}' is a template. Copy it to your contracts first using POST /contracts with from_template.",
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract '{request.contract_id}' not found",
        )
    
    # Create job record in database
    job = db_create_job(user.id, contract_uuid, {
        "num_runs": request.num_runs,
        "temperature": request.temperature,
        "model": request.model,
    })
    
    # Increment user's run count
    increment_runs(user.id, request.num_runs)
    
    # Estimate duration (rough: 2-5 seconds per LLM call)
    estimated_seconds = request.num_runs * 3
    
    # Queue job with Celery for execution
    if CELERY_AVAILABLE:
        try:
            execute_skyt_job.delay(
                job_id=str(job["id"]),
                user_id=str(user.id),
                contract_id=str(contract_uuid),
                num_runs=request.num_runs,
                temperature=request.temperature,
                model=request.model,
                restriction_ids=[str(r) for r in request.restriction_ids],
            )
            message = "Job queued for execution"
        except Exception as e:
            # Celery not available or failed - job stays queued
            message = f"Job created but worker not available: {e}"
    else:
        message = "Job created (worker not available - run manually)"
    
    return PipelineRunResponse(
        job_id=UUID(job["id"]),
        status="queued",
        message=message,
        estimated_duration_seconds=estimated_seconds,
    )


@router.get("/jobs", response_model=List[JobSummary])
async def list_jobs(
    user: User = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0,
):
    """
    List pipeline jobs for the current user.
    
    Supports pagination. Jobs are sorted by creation date (newest first).
    """
    jobs = db_get_jobs(user.id, limit=limit, offset=offset)
    
    return [
        JobSummary(
            job_id=UUID(j["id"]),
            contract_id=j.get("contracts", {}).get("contract_id", "unknown"),
            status=j["status"],
            num_runs=j["num_runs"],
            temperature=float(j["temperature"]),
            created_at=j["created_at"],
        )
        for j in jobs
    ]
