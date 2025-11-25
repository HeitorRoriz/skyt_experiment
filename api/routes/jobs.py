# api/routes/jobs.py
"""
Job management endpoints.

Get job status, results, and manage job lifecycle.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from .auth import get_current_user, User
from .pipeline import get_job, _mock_jobs


router = APIRouter(prefix="/jobs")


# =============================================================================
# Response Models
# =============================================================================

class RunResult(BaseModel):
    """Result of a single LLM run."""
    run_index: int
    raw_output: str
    canonical_output: Optional[str] = None
    oracle_passed: bool = False
    distance_to_canon: float = 1.0


class JobMetrics(BaseModel):
    """Aggregate metrics for a job."""
    R_raw: float
    R_anchor_pre: float
    R_anchor_post: float
    Delta_rescue: float
    R_behavioral: float
    R_structural: float
    rescue_rate: float
    canon_coverage: float


class JobDetail(BaseModel):
    """Detailed job information including results."""
    job_id: UUID
    user_id: UUID
    contract_id: str
    status: str
    num_runs: int
    temperature: float
    model: str
    restriction_ids: List[UUID]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    metrics: Optional[JobMetrics]
    canonical_anchor: Optional[str]
    runs: Optional[List[RunResult]]
    error: Optional[str]
    duration_ms: Optional[float]


class JobProgress(BaseModel):
    """Real-time job progress."""
    job_id: UUID
    phase: str
    completed_runs: int
    total_runs: int
    progress_percent: float
    current_run_status: Optional[str]
    estimated_completion: Optional[datetime]


class CancelResponse(BaseModel):
    """Response to job cancellation request."""
    job_id: UUID
    status: str
    message: str


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/{job_id}", response_model=JobDetail)
async def get_job_details(
    job_id: UUID,
    user: User = Depends(get_current_user),
):
    """
    Get detailed information about a job.
    
    Returns full job details including metrics and run results if completed.
    """
    job = get_job(user.id, job_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )
    
    # Calculate duration if completed
    duration_ms = None
    if job.get("started_at") and job.get("completed_at"):
        delta = job["completed_at"] - job["started_at"]
        duration_ms = delta.total_seconds() * 1000
    
    return JobDetail(
        job_id=job["job_id"],
        user_id=job["user_id"],
        contract_id=job["contract_id"],
        status=job["status"],
        num_runs=job["num_runs"],
        temperature=job["temperature"],
        model=job["model"],
        restriction_ids=job["restriction_ids"],
        created_at=job["created_at"],
        started_at=job.get("started_at"),
        completed_at=job.get("completed_at"),
        metrics=job.get("metrics"),
        canonical_anchor=job.get("canonical_anchor"),
        runs=job.get("runs"),
        error=job.get("error"),
        duration_ms=duration_ms,
    )


@router.get("/{job_id}/results")
async def get_job_results(
    job_id: UUID,
    user: User = Depends(get_current_user),
):
    """
    Get job results (metrics and outputs).
    
    Returns 202 if job is still running, 200 with results if completed.
    """
    job = get_job(user.id, job_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )
    
    if job["status"] == "queued":
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail="Job is queued, not yet started",
        )
    
    if job["status"] == "running":
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail="Job is still running",
        )
    
    if job["status"] == "failed":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Job failed: {job.get('error', 'Unknown error')}",
        )
    
    return {
        "job_id": str(job["job_id"]),
        "status": job["status"],
        "metrics": job.get("metrics"),
        "canonical_anchor": job.get("canonical_anchor"),
        "runs_count": len(job.get("runs", [])),
    }


@router.post("/{job_id}/cancel", response_model=CancelResponse)
async def cancel_job(
    job_id: UUID,
    user: User = Depends(get_current_user),
):
    """
    Cancel a running or queued job.
    
    Cancellation is best-effort. Jobs in progress will stop at the next
    check point (between LLM calls).
    """
    job = get_job(user.id, job_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )
    
    if job["status"] not in ["queued", "running"]:
        return CancelResponse(
            job_id=job_id,
            status=job["status"],
            message=f"Job cannot be cancelled (status: {job['status']})",
        )
    
    # TODO: Send cancellation signal via Redis
    # redis.set(f"job:{job_id}:cancel", "1", ex=3600)
    
    # Update job status
    _mock_jobs[str(job_id)]["status"] = "cancelled"
    
    return CancelResponse(
        job_id=job_id,
        status="cancelled",
        message="Cancellation requested",
    )


@router.get("/{job_id}/progress", response_model=JobProgress)
async def get_job_progress(
    job_id: UUID,
    user: User = Depends(get_current_user),
):
    """
    Get current progress for a running job.
    
    For real-time updates, use the WebSocket endpoint instead.
    """
    job = get_job(user.id, job_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )
    
    # TODO: Get real progress from Redis
    # For now, return mock progress
    completed = 0 if job["status"] == "queued" else job["num_runs"] if job["status"] == "completed" else job["num_runs"] // 2
    
    return JobProgress(
        job_id=job_id,
        phase=job["status"],
        completed_runs=completed,
        total_runs=job["num_runs"],
        progress_percent=(completed / job["num_runs"]) * 100 if job["num_runs"] > 0 else 0,
        current_run_status="completed" if job["status"] == "completed" else "in_progress",
        estimated_completion=None,
    )


# =============================================================================
# WebSocket for Real-Time Updates
# =============================================================================

@router.websocket("/{job_id}/stream")
async def job_progress_stream(
    websocket: WebSocket,
    job_id: UUID,
):
    """
    WebSocket endpoint for real-time job progress updates.
    
    Connect to receive live updates as the job executes:
    - Phase changes
    - Per-run completion
    - Metrics as they're computed
    
    Example client:
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/api/v1/jobs/{job_id}/stream');
    ws.onmessage = (event) => {
        const progress = JSON.parse(event.data);
        console.log(`Progress: ${progress.completed_runs}/${progress.total_runs}`);
    };
    ```
    """
    await websocket.accept()
    
    try:
        # TODO: Authenticate WebSocket connection
        # TODO: Subscribe to Redis pub/sub channel for this job
        
        # For now, send mock updates
        import asyncio
        import json
        
        job = _mock_jobs.get(str(job_id))
        if not job:
            await websocket.send_json({"error": "Job not found"})
            await websocket.close()
            return
        
        # Simulate progress updates
        for i in range(job["num_runs"] + 1):
            progress = {
                "job_id": str(job_id),
                "phase": "generating_outputs",
                "completed_runs": i,
                "total_runs": job["num_runs"],
                "progress_percent": (i / job["num_runs"]) * 100,
                "current_run_index": i if i < job["num_runs"] else None,
            }
            await websocket.send_json(progress)
            await asyncio.sleep(0.5)  # Simulate delay
        
        # Send completion
        await websocket.send_json({
            "job_id": str(job_id),
            "phase": "completed",
            "completed_runs": job["num_runs"],
            "total_runs": job["num_runs"],
            "progress_percent": 100,
            "message": "Job completed",
        })
        
    except WebSocketDisconnect:
        pass
    finally:
        await websocket.close()
