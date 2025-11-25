# src/core/interfaces.py
"""
Core Interface Definitions (Ports)

This module defines the abstract interfaces (protocols) that the SKYT core
depends on. Concrete implementations (adapters) are provided elsewhere,
enabling dependency inversion and testability.

Design Principles:
    - High-level policy depends on abstractions, not concretions (DIP)
    - Each interface is small and focused (ISP)
    - Interfaces define WHAT, implementations define HOW

Adapters by Context:
    Production SaaS:
        - OpenAIProvider, AnthropicProvider (LlmClient)
        - PostgresContractRepository (ContractRepository)
        - PostgresResultStore (ResultStore)
        - RedisCache (Cache)
        - RedisProgressReporter (ProgressReporter)
    
    Local CLI:
        - OpenAIProvider (LlmClient)
        - FileContractRepository (ContractRepository)
        - FileResultStore (ResultStore)
        - InMemoryCache (Cache)
        - ConsoleProgressReporter (ProgressReporter)
    
    Unit Tests:
        - MockLlmClient (LlmClient)
        - InMemoryContractRepository (ContractRepository)
        - InMemoryResultStore (ResultStore)
        - InMemoryCache (Cache)
        - NoOpProgressReporter (ProgressReporter)
"""

from typing import Protocol, Optional, List, Dict, Any, runtime_checkable
from uuid import UUID
from datetime import datetime


# =============================================================================
# Forward References (defined in models.py)
# =============================================================================
# These are referenced by type hints but defined in models.py to avoid
# circular imports. Using string literals for forward references.


# =============================================================================
# LLM Client Interface
# =============================================================================

@runtime_checkable
class LlmClient(Protocol):
    """
    Port for LLM code generation.
    
    Decouples core logic from specific LLM providers (OpenAI, Anthropic, etc.).
    All LLM interactions in the system go through this interface.
    
    Implementations:
        - OpenAIProvider: Uses OpenAI API (gpt-4, gpt-4-turbo, etc.)
        - AnthropicProvider: Uses Anthropic API (claude-3, etc.)
        - OpenRouterProvider: Uses OpenRouter API (multiple models)
        - MockLlmClient: Returns canned responses for testing
    """
    
    async def generate(
        self,
        prompt: str,
        pins: "ModelPins",
    ) -> "LlmOutput":
        """
        Generate code from prompt using the configured LLM.
        
        Args:
            prompt: The full prompt including contract and constraints
            pins: Model configuration (model name, temperature, seed, etc.)
        
        Returns:
            LlmOutput with generated content and usage metadata
        
        Raises:
            RateLimitError: When provider rate limits are hit
            AuthenticationError: When API key is invalid
            TimeoutError: When request times out
            LlmError: For other LLM-related errors
        """
        ...
    
    def get_info(self) -> Dict[str, str]:
        """
        Get information about the configured provider and model.
        
        Returns:
            Dict with 'provider' and 'model' keys
        """
        ...


# =============================================================================
# Repository Interfaces
# =============================================================================

@runtime_checkable
class ContractRepository(Protocol):
    """
    Port for contract storage and retrieval.
    
    Decouples core logic from contract storage mechanism (filesystem, database).
    Supports both preset contracts (read-only) and user-defined contracts.
    
    Implementations:
        - FileContractRepository: Reads from JSON files (CLI mode)
        - PostgresContractRepository: Reads from database (SaaS mode)
        - InMemoryContractRepository: For testing
    """
    
    def get(
        self,
        user_id: Optional[UUID],
        contract_id: str,
        version: Optional[str] = None,
    ) -> "Contract":
        """
        Retrieve a contract by ID.
        
        Args:
            user_id: User ID (None for preset contracts)
            contract_id: Contract identifier
            version: Specific version (None for latest)
        
        Returns:
            Contract object
        
        Raises:
            ContractNotFoundError: When contract doesn't exist
        """
        ...
    
    def list(
        self,
        user_id: Optional[UUID],
        include_presets: bool = True,
    ) -> List["Contract"]:
        """
        List available contracts for a user.
        
        Args:
            user_id: User ID (None for presets only)
            include_presets: Whether to include preset contracts
        
        Returns:
            List of Contract objects
        """
        ...


@runtime_checkable
class RestrictionRepository(Protocol):
    """
    Port for restriction set storage and retrieval.
    
    Restriction sets define coding standards and constraints (NASA Power of 10,
    MISRA-C, DO-178C, etc.). Supports both presets and user-defined sets.
    
    Implementations:
        - FileRestrictionRepository: Reads from JSON files
        - PostgresRestrictionRepository: Reads from database
        - InMemoryRestrictionRepository: For testing
    """
    
    def get(
        self,
        user_id: Optional[UUID],
        restriction_id: UUID,
        version: Optional[str] = None,
    ) -> "RestrictionSet":
        """
        Retrieve a restriction set by ID.
        
        Args:
            user_id: User ID (None for presets)
            restriction_id: Restriction set UUID
            version: Specific version (None for latest)
        
        Returns:
            RestrictionSet object
        
        Raises:
            RestrictionNotFoundError: When restriction set doesn't exist
        """
        ...
    
    def get_many(
        self,
        user_id: Optional[UUID],
        restriction_ids: List[UUID],
    ) -> List["RestrictionSet"]:
        """
        Retrieve multiple restriction sets by ID.
        
        Args:
            user_id: User ID (None for presets)
            restriction_ids: List of restriction set UUIDs
        
        Returns:
            List of RestrictionSet objects (in same order as IDs)
        
        Raises:
            RestrictionNotFoundError: When any restriction set doesn't exist
        """
        ...
    
    def list_presets(self) -> List["RestrictionSet"]:
        """
        List all available preset restriction sets.
        
        Returns:
            List of preset RestrictionSet objects
        """
        ...


# =============================================================================
# Storage Interfaces
# =============================================================================

@runtime_checkable
class ResultStore(Protocol):
    """
    Port for job result persistence.
    
    Stores job results including metrics, outputs, and configuration snapshots.
    Supports both hot storage (database) and cold storage (object store).
    
    Implementations:
        - FileResultStore: Saves to local JSON files (CLI mode)
        - PostgresResultStore: Saves to PostgreSQL (SaaS mode)
        - S3ResultStore: Saves artifacts to S3 (large outputs)
        - InMemoryResultStore: For testing
    """
    
    def save(
        self,
        job_id: UUID,
        result: "JobResult",
    ) -> None:
        """
        Save job result.
        
        Args:
            job_id: Job UUID
            result: JobResult object to persist
        
        Raises:
            StorageError: When save fails
        """
        ...
    
    def get(
        self,
        job_id: UUID,
    ) -> Optional["JobResult"]:
        """
        Retrieve job result.
        
        Args:
            job_id: Job UUID
        
        Returns:
            JobResult if found, None otherwise
        """
        ...
    
    def list_by_user(
        self,
        user_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> List["JobResult"]:
        """
        List job results for a user.
        
        Args:
            user_id: User UUID
            limit: Maximum results to return
            offset: Pagination offset
        
        Returns:
            List of JobResult objects
        """
        ...


@runtime_checkable
class Cache(Protocol):
    """
    Port for caching.
    
    Provides fast access to frequently used data (contracts, canons, etc.).
    Supports TTL-based expiration and explicit invalidation.
    
    Implementations:
        - RedisCache: Uses Redis (SaaS mode)
        - MemcachedCache: Uses Memcached (alternative)
        - InMemoryCache: Simple dict-based (CLI mode, testing)
    """
    
    def get(self, key: str) -> Optional[bytes]:
        """
        Retrieve cached value.
        
        Args:
            key: Cache key
        
        Returns:
            Cached bytes if found, None otherwise
        """
        ...
    
    def set(
        self,
        key: str,
        value: bytes,
        ttl_seconds: Optional[int] = None,
    ) -> None:
        """
        Store value in cache.
        
        Args:
            key: Cache key
            value: Value to cache (as bytes)
            ttl_seconds: Time-to-live in seconds (None for no expiry)
        """
        ...
    
    def invalidate(self, key: str) -> None:
        """
        Remove value from cache.
        
        Args:
            key: Cache key to invalidate
        """
        ...
    
    def invalidate_pattern(self, pattern: str) -> int:
        """
        Remove all values matching pattern.
        
        Args:
            pattern: Glob pattern (e.g., "contract:*")
        
        Returns:
            Number of keys invalidated
        """
        ...


# =============================================================================
# Progress Reporting Interface
# =============================================================================

@runtime_checkable
class ProgressReporter(Protocol):
    """
    Port for job progress reporting.
    
    Enables real-time visibility into job execution, especially LLM calls.
    Supports both push (pub/sub) and pull (state query) patterns.
    
    Implementations:
        - RedisProgressReporter: Pub/sub + state storage (SaaS mode)
        - ConsoleProgressReporter: Prints to stdout (CLI mode)
        - NoOpProgressReporter: Does nothing (testing, batch mode)
    """
    
    def update_phase(
        self,
        job_id: UUID,
        phase: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Update job phase.
        
        Args:
            job_id: Job UUID
            phase: New phase name (from JobPhase enum)
            metadata: Optional phase-specific metadata
        """
        ...
    
    def update_llm_call(
        self,
        job_id: UUID,
        run_index: int,
        status: str,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        duration_ms: Optional[float] = None,
        tokens_used: Optional[int] = None,
        error: Optional[str] = None,
    ) -> None:
        """
        Update LLM call status.
        
        Args:
            job_id: Job UUID
            run_index: Which run (0-indexed)
            status: "pending", "in_progress", "completed", "failed"
            started_at: When the call started
            completed_at: When the call completed
            duration_ms: Call duration in milliseconds
            tokens_used: Total tokens consumed
            error: Error message if failed
        """
        ...
    
    def update_progress(
        self,
        job_id: UUID,
        completed_runs: int,
        total_runs: int,
        estimated_completion: Optional[datetime] = None,
    ) -> None:
        """
        Update overall progress.
        
        Args:
            job_id: Job UUID
            completed_runs: Number of completed runs
            total_runs: Total number of runs
            estimated_completion: Estimated completion time
        """
        ...
    
    def mark_completed(
        self,
        job_id: UUID,
        metrics_summary: Dict[str, Any],
    ) -> None:
        """
        Mark job as completed with final metrics.
        
        Args:
            job_id: Job UUID
            metrics_summary: Final metrics (R_raw, R_anchor, etc.)
        """
        ...
    
    def mark_failed(
        self,
        job_id: UUID,
        error: str,
        phase: Optional[str] = None,
    ) -> None:
        """
        Mark job as failed.
        
        Args:
            job_id: Job UUID
            error: Error message
            phase: Phase where failure occurred
        """
        ...


# =============================================================================
# Custom Exceptions
# =============================================================================

class SkytError(Exception):
    """Base exception for SKYT errors."""
    pass


class ContractNotFoundError(SkytError):
    """Raised when a contract is not found."""
    def __init__(self, contract_id: str):
        self.contract_id = contract_id
        super().__init__(f"Contract not found: {contract_id}")


class RestrictionNotFoundError(SkytError):
    """Raised when a restriction set is not found."""
    def __init__(self, restriction_id: UUID):
        self.restriction_id = restriction_id
        super().__init__(f"Restriction set not found: {restriction_id}")


class LlmError(SkytError):
    """Base exception for LLM-related errors."""
    pass


class RateLimitError(LlmError):
    """Raised when LLM provider rate limits are hit."""
    def __init__(self, retry_after: Optional[float] = None):
        self.retry_after = retry_after
        msg = "Rate limit exceeded"
        if retry_after:
            msg += f", retry after {retry_after}s"
        super().__init__(msg)


class AuthenticationError(LlmError):
    """Raised when LLM API authentication fails."""
    pass


class StorageError(SkytError):
    """Raised when storage operations fail."""
    pass
