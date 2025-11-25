# src/core/progress.py
"""
Job Progress Tracking

This module provides data structures for tracking job execution progress,
with granular visibility into each LLM call.

Designed to solve the "black box" problem with background job execution:
- Which phase is the job in?
- Which LLM call is currently running?
- How long until completion?
- Can I cancel it?
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID
import json


class JobPhase(Enum):
    """
    Job execution phases.
    
    Granular phases enable precise progress tracking and debugging.
    Each phase represents a distinct stage in the pipeline.
    """
    QUEUED = "queued"
    LOADING_CONTRACT = "loading_contract"
    LOADING_RESTRICTIONS = "loading_restrictions"
    GENERATING_OUTPUTS = "generating_outputs"  # LLM calls happen here
    CANONICALIZING = "canonicalizing"
    COMPUTING_METRICS = "computing_metrics"
    SAVING_RESULTS = "saving_results"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    
    @property
    def is_terminal(self) -> bool:
        """Whether this phase is a terminal state."""
        return self in (JobPhase.COMPLETED, JobPhase.FAILED, JobPhase.CANCELLED)
    
    @property
    def is_active(self) -> bool:
        """Whether job is actively processing."""
        return self not in (JobPhase.QUEUED, JobPhase.COMPLETED, 
                           JobPhase.FAILED, JobPhase.CANCELLED)


@dataclass
class LLMCallStatus:
    """
    Status of a single LLM API call.
    
    Tracks timing, token usage, and outcome for each generation run.
    Enables per-call visibility and debugging.
    
    Attributes:
        run_index: Which run (0-indexed)
        status: "pending", "in_progress", "completed", "failed"
        started_at: When the call started
        completed_at: When the call completed
        duration_ms: Call duration in milliseconds
        tokens_prompt: Prompt tokens consumed
        tokens_completion: Completion tokens generated
        tokens_total: Total tokens (prompt + completion)
        error: Error message if failed
    """
    run_index: int
    status: str = "pending"  # pending, in_progress, completed, failed
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[float] = None
    tokens_prompt: Optional[int] = None
    tokens_completion: Optional[int] = None
    tokens_total: Optional[int] = None
    error: Optional[str] = None
    
    @property
    def is_complete(self) -> bool:
        return self.status in ("completed", "failed")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_index": self.run_index,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms,
            "tokens_prompt": self.tokens_prompt,
            "tokens_completion": self.tokens_completion,
            "tokens_total": self.tokens_total,
            "error": self.error,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LLMCallStatus":
        return cls(
            run_index=data["run_index"],
            status=data.get("status", "pending"),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            duration_ms=data.get("duration_ms"),
            tokens_prompt=data.get("tokens_prompt"),
            tokens_completion=data.get("tokens_completion"),
            tokens_total=data.get("tokens_total"),
            error=data.get("error"),
        )


@dataclass
class JobProgress:
    """
    Complete job progress state.
    
    Aggregates all progress information for a job, including:
    - Current phase
    - Overall progress (completed/total runs)
    - Per-run LLM call status
    - Time estimates
    
    This is the primary data structure sent via WebSocket/SSE for
    real-time progress updates.
    """
    job_id: UUID
    phase: JobPhase
    phase_started_at: datetime = field(default_factory=datetime.utcnow)
    
    # Overall progress
    total_runs: int = 0
    completed_runs: int = 0
    
    # Per-run tracking
    runs: List[LLMCallStatus] = field(default_factory=list)
    current_run_index: Optional[int] = None
    
    # Time tracking
    job_started_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    avg_run_duration_ms: Optional[float] = None
    
    # Error tracking
    error: Optional[str] = None
    error_phase: Optional[str] = None
    
    @property
    def progress_percent(self) -> float:
        """Progress as percentage (0-100)."""
        if self.total_runs == 0:
            return 0.0
        return (self.completed_runs / self.total_runs) * 100
    
    @property
    def current_run(self) -> Optional[LLMCallStatus]:
        """Get the currently executing run, if any."""
        if self.current_run_index is not None and self.current_run_index < len(self.runs):
            return self.runs[self.current_run_index]
        return None
    
    @property
    def total_tokens_used(self) -> int:
        """Sum of tokens across all completed runs."""
        return sum(
            r.tokens_total or 0
            for r in self.runs
            if r.status == "completed"
        )
    
    @property
    def total_duration_ms(self) -> float:
        """Sum of durations across all completed runs."""
        return sum(
            r.duration_ms or 0
            for r in self.runs
            if r.status == "completed"
        )
    
    def update_estimates(self) -> None:
        """Recalculate time estimates based on completed runs."""
        completed = [r for r in self.runs if r.status == "completed" and r.duration_ms]
        if completed:
            self.avg_run_duration_ms = sum(r.duration_ms for r in completed) / len(completed)
            remaining = self.total_runs - self.completed_runs
            if remaining > 0 and self.avg_run_duration_ms:
                remaining_ms = remaining * self.avg_run_duration_ms
                self.estimated_completion = datetime.utcnow() + \
                    __import__('datetime').timedelta(milliseconds=remaining_ms)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "job_id": str(self.job_id),
            "phase": self.phase.value,
            "phase_started_at": self.phase_started_at.isoformat(),
            "total_runs": self.total_runs,
            "completed_runs": self.completed_runs,
            "progress_percent": round(self.progress_percent, 1),
            "runs": [r.to_dict() for r in self.runs],
            "current_run_index": self.current_run_index,
            "current_run": self.current_run.to_dict() if self.current_run else None,
            "job_started_at": self.job_started_at.isoformat() if self.job_started_at else None,
            "estimated_completion": self.estimated_completion.isoformat() if self.estimated_completion else None,
            "avg_run_duration_ms": self.avg_run_duration_ms,
            "total_tokens_used": self.total_tokens_used,
            "total_duration_ms": self.total_duration_ms,
            "error": self.error,
            "error_phase": self.error_phase,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JobProgress":
        """Create from dictionary."""
        return cls(
            job_id=UUID(data["job_id"]),
            phase=JobPhase(data["phase"]),
            phase_started_at=datetime.fromisoformat(data["phase_started_at"]),
            total_runs=data.get("total_runs", 0),
            completed_runs=data.get("completed_runs", 0),
            runs=[LLMCallStatus.from_dict(r) for r in data.get("runs", [])],
            current_run_index=data.get("current_run_index"),
            job_started_at=datetime.fromisoformat(data["job_started_at"]) if data.get("job_started_at") else None,
            estimated_completion=datetime.fromisoformat(data["estimated_completion"]) if data.get("estimated_completion") else None,
            avg_run_duration_ms=data.get("avg_run_duration_ms"),
            error=data.get("error"),
            error_phase=data.get("error_phase"),
        )
    
    @classmethod
    def create(cls, job_id: UUID, total_runs: int) -> "JobProgress":
        """Factory method to create initial progress state."""
        return cls(
            job_id=job_id,
            phase=JobPhase.QUEUED,
            total_runs=total_runs,
            runs=[LLMCallStatus(run_index=i) for i in range(total_runs)],
        )
