# src/core/__init__.py
"""
SKYT Core Layer

This package provides the foundational abstractions and orchestration logic
for the SKYT system. It follows the Dependency Inversion Principle (DIP):
high-level policy depends on abstractions, not concrete implementations.

Architecture:
    interfaces.py     - Protocol definitions (ports)
    models.py         - Domain dataclasses
    progress.py       - Job progress tracking
    observable_llm.py - LLM wrapper with observability
    pipeline.py       - Main orchestrator (future)

Usage:
    from src.core import LlmClient, Pipeline, JobProgress
    from src.core.models import ExperimentConfig, JobResult
"""

from .interfaces import (
    LlmClient,
    ContractRepository,
    RestrictionRepository,
    ResultStore,
    Cache,
    ProgressReporter,
)

from .models import (
    ModelPins,
    LlmOutput,
    ExperimentConfig,
    RunResult,
    JobResult,
)

from .progress import (
    JobPhase,
    LLMCallStatus,
    JobProgress,
)

from .observable_llm import (
    LLMCallMetrics,
    ObservableLLMClient,
)

__all__ = [
    # Interfaces (Protocols)
    "LlmClient",
    "ContractRepository",
    "RestrictionRepository",
    "ResultStore",
    "Cache",
    "ProgressReporter",
    # Models
    "ModelPins",
    "LlmOutput",
    "ExperimentConfig",
    "RunResult",
    "JobResult",
    # Progress
    "JobPhase",
    "LLMCallStatus",
    "JobProgress",
    # Observable LLM
    "LLMCallMetrics",
    "ObservableLLMClient",
]
