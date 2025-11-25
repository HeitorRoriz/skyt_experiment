# src/core/observable_llm.py
"""
Observable LLM Client Wrapper

Wraps any LLM client implementation with observability hooks for:
- Call start/end events
- Duration tracking
- Token usage capture
- Error classification

This enables real-time progress reporting without modifying the
underlying LLM client implementations.

Usage:
    from src.core.observable_llm import ObservableLLMClient
    
    def on_start(run_index: int):
        print(f"Starting run {run_index}")
    
    def on_end(run_index: int, metrics: LLMCallMetrics):
        print(f"Run {run_index} completed in {metrics.duration_ms}ms")
    
    observable = ObservableLLMClient(
        base_client=openai_client,
        on_call_start=on_start,
        on_call_end=on_end,
    )
    
    result = await observable.generate(prompt, pins, run_index=0)
"""

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Callable, Dict, Any, Awaitable

from .models import ModelPins, LlmOutput
from .interfaces import LlmClient, RateLimitError


@dataclass
class LLMCallMetrics:
    """
    Metrics captured from a single LLM API call.
    
    Provides detailed visibility into each call for:
    - Performance monitoring
    - Cost tracking
    - Debugging
    - Rate limit handling
    
    Attributes:
        run_index: Which run this call belongs to
        model: Model used for generation
        started_at: Call start timestamp
        completed_at: Call completion timestamp
        duration_ms: Total call duration in milliseconds
        tokens_prompt: Prompt tokens consumed
        tokens_completion: Completion tokens generated
        tokens_total: Total tokens (prompt + completion)
        status: Outcome status
        error: Error message if failed
        error_type: Error classification
        retry_after: Seconds to wait before retry (rate limits)
    """
    run_index: int
    model: str
    started_at: float  # time.time()
    completed_at: Optional[float] = None
    duration_ms: Optional[float] = None
    tokens_prompt: Optional[int] = None
    tokens_completion: Optional[int] = None
    tokens_total: Optional[int] = None
    status: str = "in_progress"  # in_progress, success, rate_limited, timeout, error
    error: Optional[str] = None
    error_type: Optional[str] = None
    retry_after: Optional[float] = None
    
    def finalize(self, success: bool = True) -> None:
        """Mark call as complete and calculate duration."""
        self.completed_at = time.time()
        self.duration_ms = (self.completed_at - self.started_at) * 1000
        if success:
            self.status = "success"
    
    def mark_error(self, error: Exception) -> None:
        """Classify and record error."""
        self.completed_at = time.time()
        self.duration_ms = (self.completed_at - self.started_at) * 1000
        self.error = str(error)
        self.error_type = type(error).__name__
        
        # Classify error type
        error_name = type(error).__name__.lower()
        if "ratelimit" in error_name or "rate_limit" in error_name:
            self.status = "rate_limited"
            if hasattr(error, "retry_after"):
                self.retry_after = error.retry_after
        elif "timeout" in error_name:
            self.status = "timeout"
        elif "auth" in error_name:
            self.status = "auth_error"
        else:
            self.status = "error"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "run_index": self.run_index,
            "model": self.model,
            "started_at": datetime.fromtimestamp(self.started_at).isoformat(),
            "completed_at": datetime.fromtimestamp(self.completed_at).isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms,
            "tokens_prompt": self.tokens_prompt,
            "tokens_completion": self.tokens_completion,
            "tokens_total": self.tokens_total,
            "status": self.status,
            "error": self.error,
            "error_type": self.error_type,
            "retry_after": self.retry_after,
        }


# Type aliases for callbacks
OnCallStart = Callable[[int], None]  # (run_index) -> None
OnCallEnd = Callable[[int, LLMCallMetrics], None]  # (run_index, metrics) -> None
AsyncOnCallStart = Callable[[int], Awaitable[None]]
AsyncOnCallEnd = Callable[[int, LLMCallMetrics], Awaitable[None]]


class ObservableLLMClient:
    """
    Wrapper that adds observability to any LLM client.
    
    Intercepts all generate() calls to:
    1. Fire on_call_start before the call
    2. Track timing and token usage
    3. Classify any errors
    4. Fire on_call_end after the call (success or failure)
    
    The wrapped client must implement the LlmClient protocol.
    
    Attributes:
        _client: The underlying LLM client
        _on_start: Callback fired before each call
        _on_end: Callback fired after each call
        _async_callbacks: Whether callbacks are async
    
    Example:
        observable = ObservableLLMClient(
            base_client=openai_provider,
            on_call_start=lambda i: reporter.update_llm_call(i, "in_progress"),
            on_call_end=lambda i, m: reporter.update_llm_call(i, m.status, 
                duration_ms=m.duration_ms, tokens_used=m.tokens_total),
        )
    """
    
    def __init__(
        self,
        base_client: LlmClient,
        on_call_start: Optional[OnCallStart] = None,
        on_call_end: Optional[OnCallEnd] = None,
        async_on_call_start: Optional[AsyncOnCallStart] = None,
        async_on_call_end: Optional[AsyncOnCallEnd] = None,
    ):
        """
        Initialize observable wrapper.
        
        Args:
            base_client: The LLM client to wrap
            on_call_start: Sync callback before each call
            on_call_end: Sync callback after each call
            async_on_call_start: Async callback before each call
            async_on_call_end: Async callback after each call
        """
        self._client = base_client
        self._on_start = on_call_start
        self._on_end = on_call_end
        self._async_on_start = async_on_call_start
        self._async_on_end = async_on_call_end
    
    async def generate(
        self,
        prompt: str,
        pins: ModelPins,
        run_index: int = 0,
    ) -> LlmOutput:
        """
        Generate code with observability.
        
        Wraps the base client's generate() with timing, metrics capture,
        and callback invocations.
        
        Args:
            prompt: The generation prompt
            pins: Model configuration
            run_index: Which run this is (for tracking)
        
        Returns:
            LlmOutput from the base client
        
        Raises:
            Same exceptions as the base client
        """
        # Initialize metrics
        metrics = LLMCallMetrics(
            run_index=run_index,
            model=pins.model,
            started_at=time.time(),
        )
        
        # Fire start callback
        await self._fire_start(run_index)
        
        try:
            # Make the actual LLM call
            result = await self._client.generate(prompt, pins)
            
            # Capture success metrics
            metrics.finalize(success=True)
            metrics.tokens_prompt = result.prompt_tokens
            metrics.tokens_completion = result.completion_tokens
            metrics.tokens_total = result.total_tokens
            
            return result
            
        except Exception as e:
            # Capture error metrics
            metrics.mark_error(e)
            raise
            
        finally:
            # Always fire end callback
            await self._fire_end(run_index, metrics)
    
    async def _fire_start(self, run_index: int) -> None:
        """Fire start callback (sync or async)."""
        if self._async_on_start:
            await self._async_on_start(run_index)
        elif self._on_start:
            self._on_start(run_index)
    
    async def _fire_end(self, run_index: int, metrics: LLMCallMetrics) -> None:
        """Fire end callback (sync or async)."""
        if self._async_on_end:
            await self._async_on_end(run_index, metrics)
        elif self._on_end:
            self._on_end(run_index, metrics)
    
    def get_info(self) -> Dict[str, str]:
        """Delegate to base client."""
        return self._client.get_info()


class SyncObservableLLMClient:
    """
    Synchronous version of ObservableLLMClient.
    
    For use in non-async contexts (CLI, Celery workers without async).
    """
    
    def __init__(
        self,
        base_client: "SyncLlmClient",
        on_call_start: Optional[OnCallStart] = None,
        on_call_end: Optional[OnCallEnd] = None,
    ):
        self._client = base_client
        self._on_start = on_call_start
        self._on_end = on_call_end
    
    def generate(
        self,
        prompt: str,
        pins: ModelPins,
        run_index: int = 0,
    ) -> LlmOutput:
        """Synchronous generate with observability."""
        metrics = LLMCallMetrics(
            run_index=run_index,
            model=pins.model,
            started_at=time.time(),
        )
        
        if self._on_start:
            self._on_start(run_index)
        
        try:
            result = self._client.generate(prompt, pins)
            
            metrics.finalize(success=True)
            metrics.tokens_prompt = result.prompt_tokens
            metrics.tokens_completion = result.completion_tokens
            metrics.tokens_total = result.total_tokens
            
            return result
            
        except Exception as e:
            metrics.mark_error(e)
            raise
            
        finally:
            if self._on_end:
                self._on_end(run_index, metrics)
    
    def get_info(self) -> Dict[str, str]:
        return self._client.get_info()
