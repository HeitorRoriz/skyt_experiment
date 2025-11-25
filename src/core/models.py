# src/core/models.py
"""
Domain Models for SKYT Core

This module defines the core domain objects used throughout the SKYT system.
These are plain dataclasses with no infrastructure dependencies.

Design Principles:
    - Immutable where possible (frozen dataclasses)
    - Serializable to JSON for persistence and API responses
    - Rich domain logic in dedicated methods
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from enum import Enum
import json


# =============================================================================
# LLM Configuration
# =============================================================================

@dataclass(frozen=True)
class ModelPins:
    """
    Pinned model configuration for reproducibility.
    
    All parameters that affect LLM output are captured here so that
    experiments can be exactly reproduced.
    
    Attributes:
        model: Model identifier (e.g., "gpt-4-turbo", "claude-3-5-sonnet")
        temperature: Sampling temperature (0.0 to 2.0)
        max_tokens: Maximum tokens to generate
        seed: Random seed for deterministic sampling (if supported)
        top_p: Nucleus sampling parameter
        frequency_penalty: Frequency penalty for repetition
        presence_penalty: Presence penalty for topic diversity
    """
    model: str
    temperature: float = 0.0
    max_tokens: int = 4096
    seed: Optional[int] = None
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelPins":
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class LlmOutput:
    """
    Output from an LLM generation call.
    
    Captures both the generated content and usage metadata for
    billing, monitoring, and analysis.
    
    Attributes:
        content: The generated text (code)
        model: Actual model used (may differ from requested)
        prompt_tokens: Number of tokens in the prompt
        completion_tokens: Number of tokens in the completion
        total_tokens: Total tokens consumed
        finish_reason: Why generation stopped ("stop", "length", etc.)
        latency_ms: Request latency in milliseconds
    """
    content: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    finish_reason: str = "stop"
    latency_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LlmOutput":
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# =============================================================================
# Experiment Configuration
# =============================================================================

@dataclass
class ExperimentConfig:
    """
    Complete experiment configuration for reproducibility.
    
    All parameters needed to exactly reproduce an experiment are captured here.
    This is stored with job results to enable replay and audit.
    
    Attributes:
        contract_id: Contract identifier
        contract_version: Contract version string
        restriction_ids: List of restriction set UUIDs applied
        restriction_versions: List of restriction set versions
        pins: Model configuration
        num_runs: Number of LLM generations
        metrics_version: Version of metrics computation
    """
    contract_id: str
    contract_version: str
    pins: ModelPins
    num_runs: int
    restriction_ids: List[UUID] = field(default_factory=list)
    restriction_versions: List[str] = field(default_factory=list)
    metrics_version: str = "2025-11-25"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "contract_id": self.contract_id,
            "contract_version": self.contract_version,
            "restriction_ids": [str(rid) for rid in self.restriction_ids],
            "restriction_versions": self.restriction_versions,
            "pins": self.pins.to_dict(),
            "num_runs": self.num_runs,
            "metrics_version": self.metrics_version,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExperimentConfig":
        """Create from dictionary."""
        return cls(
            contract_id=data["contract_id"],
            contract_version=data["contract_version"],
            restriction_ids=[UUID(rid) for rid in data.get("restriction_ids", [])],
            restriction_versions=data.get("restriction_versions", []),
            pins=ModelPins.from_dict(data["pins"]),
            num_runs=data["num_runs"],
            metrics_version=data.get("metrics_version", "2025-11-25"),
        )
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


# =============================================================================
# Run Results
# =============================================================================

@dataclass
class RunResult:
    """
    Result of a single LLM generation run.
    
    Captures raw output, canonicalized output, and per-run metrics.
    
    Attributes:
        run_index: 0-indexed run number
        raw_output: Original LLM output (code as generated)
        canonical_output: Canonicalized output (after transformations)
        oracle_passed: Whether output passed behavioral oracle
        distance_to_canon: Structural distance to canonical anchor
        llm_output: Full LLM response metadata
        transformations_applied: List of transformations applied
    """
    run_index: int
    raw_output: str
    canonical_output: Optional[str] = None
    oracle_passed: bool = False
    distance_to_canon: float = 1.0
    llm_output: Optional[LlmOutput] = None
    transformations_applied: List[str] = field(default_factory=list)
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "run_index": self.run_index,
            "raw_output": self.raw_output,
            "canonical_output": self.canonical_output,
            "oracle_passed": self.oracle_passed,
            "distance_to_canon": self.distance_to_canon,
            "llm_output": self.llm_output.to_dict() if self.llm_output else None,
            "transformations_applied": self.transformations_applied,
            "error": self.error,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RunResult":
        """Create from dictionary."""
        return cls(
            run_index=data["run_index"],
            raw_output=data["raw_output"],
            canonical_output=data.get("canonical_output"),
            oracle_passed=data.get("oracle_passed", False),
            distance_to_canon=data.get("distance_to_canon", 1.0),
            llm_output=LlmOutput.from_dict(data["llm_output"]) if data.get("llm_output") else None,
            transformations_applied=data.get("transformations_applied", []),
            error=data.get("error"),
        )


# =============================================================================
# Job Results
# =============================================================================

class JobStatus(Enum):
    """Job execution status."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class JobResult:
    """
    Complete result of a SKYT job.
    
    Contains all run results, aggregate metrics, and configuration snapshot.
    This is the primary output of the Pipeline and is persisted for audit.
    
    Attributes:
        job_id: Unique job identifier
        user_id: User who submitted the job
        config: Experiment configuration snapshot
        status: Job execution status
        runs: List of individual run results
        metrics: Aggregate metrics (R_raw, R_anchor, etc.)
        canonical_anchor: The canonical reference (first compliant output)
        created_at: When job was created
        started_at: When job started executing
        completed_at: When job finished
        error: Error message if failed
    """
    job_id: UUID
    user_id: Optional[UUID]
    config: ExperimentConfig
    status: JobStatus = JobStatus.QUEUED
    runs: List[RunResult] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    canonical_anchor: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    
    @property
    def duration_ms(self) -> Optional[float]:
        """Calculate job duration in milliseconds."""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return delta.total_seconds() * 1000
        return None
    
    @property
    def total_tokens(self) -> int:
        """Sum of all tokens used across runs."""
        return sum(
            r.llm_output.total_tokens
            for r in self.runs
            if r.llm_output
        )
    
    @property
    def successful_runs(self) -> int:
        """Count of runs that passed oracle."""
        return sum(1 for r in self.runs if r.oracle_passed)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "job_id": str(self.job_id),
            "user_id": str(self.user_id) if self.user_id else None,
            "config": self.config.to_dict(),
            "status": self.status.value,
            "runs": [r.to_dict() for r in self.runs],
            "metrics": self.metrics,
            "canonical_anchor": self.canonical_anchor,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "total_tokens": self.total_tokens,
            "successful_runs": self.successful_runs,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JobResult":
        """Create from dictionary."""
        return cls(
            job_id=UUID(data["job_id"]),
            user_id=UUID(data["user_id"]) if data.get("user_id") else None,
            config=ExperimentConfig.from_dict(data["config"]),
            status=JobStatus(data.get("status", "queued")),
            runs=[RunResult.from_dict(r) for r in data.get("runs", [])],
            metrics=data.get("metrics", {}),
            canonical_anchor=data.get("canonical_anchor"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.utcnow(),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            error=data.get("error"),
        )
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def create(
        cls,
        config: ExperimentConfig,
        user_id: Optional[UUID] = None,
        job_id: Optional[UUID] = None,
    ) -> "JobResult":
        """Factory method to create a new job result."""
        return cls(
            job_id=job_id or uuid4(),
            user_id=user_id,
            config=config,
            status=JobStatus.QUEUED,
            created_at=datetime.utcnow(),
        )


# =============================================================================
# Contract and Restriction Models (simplified for interface compatibility)
# =============================================================================

@dataclass
class Contract:
    """
    Simplified contract model for interface compatibility.
    
    The full contract schema is defined in src/contract.py.
    This is a minimal representation for the core interfaces.
    """
    id: str
    version: str
    task_intent: str
    prompt: str
    constraints: Dict[str, Any] = field(default_factory=dict)
    oracle_requirements: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RestrictionSet:
    """
    Simplified restriction set model for interface compatibility.
    
    Restriction sets define coding standards and constraints.
    """
    id: UUID
    name: str
    version: str
    source: str  # "user" or "preset"
    rules: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["id"] = str(self.id)
        return result
