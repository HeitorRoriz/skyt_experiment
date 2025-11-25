# api/routes/pipeline.py
"""
Pipeline endpoints.

Submit and manage SKYT pipeline jobs.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field

from .auth import get_current_user, User


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
# Mock Job Store (Replace with database + Celery in production)
# =============================================================================

_mock_jobs = {}


def create_job(user_id: UUID, request: PipelineRunRequest) -> dict:
    """Create a new job record."""
    job_id = uuid4()
    job = {
        "job_id": job_id,
        "user_id": user_id,
        "contract_id": request.contract_id,
        "num_runs": request.num_runs,
        "temperature": request.temperature,
        "model": request.model,
        "restriction_ids": request.restriction_ids,
        "client_job_id": request.client_job_id,
        "status": "queued",
        "created_at": datetime.utcnow(),
        "started_at": None,
        "completed_at": None,
        "metrics": None,
        "error": None,
    }
    _mock_jobs[str(job_id)] = job
    return job


def get_job(user_id: UUID, job_id: UUID) -> Optional[dict]:
    """Get job by ID, scoped to user."""
    job = _mock_jobs.get(str(job_id))
    if job and job["user_id"] == user_id:
        return job
    return None


def get_job_by_client_id(user_id: UUID, client_job_id: str) -> Optional[dict]:
    """Get job by client-provided ID."""
    for job in _mock_jobs.values():
        if job["user_id"] == user_id and job["client_job_id"] == client_job_id:
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
    # Check for idempotent request
    if request.client_job_id:
        existing = get_job_by_client_id(user.id, request.client_job_id)
        if existing:
            return PipelineRunResponse(
                job_id=existing["job_id"],
                status=existing["status"],
                message="Existing job returned (idempotent)",
            )
    
    # TODO: Check user quota
    # TODO: Validate contract exists
    # TODO: Validate restriction_ids exist
    
    # Create job record
    job = create_job(user.id, request)
    
    # TODO: Queue job with Celery
    # background_tasks.add_task(execute_job, job["job_id"])
    
    # Estimate duration (rough: 2-5 seconds per LLM call)
    estimated_seconds = request.num_runs * 3
    
    return PipelineRunResponse(
        job_id=job["job_id"],
        status="queued",
        message="Job queued successfully",
        estimated_duration_seconds=estimated_seconds,
    )


@router.get("/jobs", response_model=List[JobSummary])
async def list_jobs(
    user: User = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0,
    status: Optional[str] = None,
):
    """
    List pipeline jobs for the current user.
    
    Supports pagination and filtering by status.
    """
    user_jobs = [
        j for j in _mock_jobs.values()
        if j["user_id"] == user.id
    ]
    
    # Filter by status
    if status:
        user_jobs = [j for j in user_jobs if j["status"] == status]
    
    # Sort by created_at descending
    user_jobs.sort(key=lambda j: j["created_at"], reverse=True)
    
    # Paginate
    user_jobs = user_jobs[offset:offset + limit]
    
    return [
        JobSummary(
            job_id=j["job_id"],
            contract_id=j["contract_id"],
            status=j["status"],
            num_runs=j["num_runs"],
            temperature=j["temperature"],
            created_at=j["created_at"],
        )
        for j in user_jobs
    ]
