# workers/tasks.py
"""
Celery Tasks for SKYT Pipeline Execution

Defines background tasks for:
- Running SKYT pipeline jobs
- Progress reporting
- Job cleanup
"""

import os
import sys
import time
import json
from datetime import datetime
from typing import Optional
from uuid import UUID
from pathlib import Path

from celery import shared_task
from celery.exceptions import Ignore, Retry
from celery.utils.log import get_task_logger

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from .celery_app import app

# Import SKYT core components
try:
    from src.llm import LLMClient
    from src.metrics import MetricsCalculator
    from src.canon_system import CanonSystem
    from src.oracle_system import OracleSystem
    from src.code_transformer import CodeTransformer
    SKYT_AVAILABLE = True
except ImportError as e:
    SKYT_AVAILABLE = False
    print(f"Warning: SKYT core not available: {e}")

# Import database operations
from api.database import (
    get_contract_by_uuid,
    update_job,
    update_job_status,
    create_job_output,
    create_job_metrics,
    get_canon_anchor,
    create_canon_anchor,
)

logger = get_task_logger(__name__)


# =============================================================================
# Redis helpers (mock for now)
# =============================================================================

class MockRedis:
    """Mock Redis client for development."""
    _data = {}
    _pubsub = {}
    
    def get(self, key: str) -> Optional[str]:
        return self._data.get(key)
    
    def set(self, key: str, value: str, ex: int = None):
        self._data[key] = value
    
    def publish(self, channel: str, message: str):
        logger.info(f"[PUBSUB] {channel}: {message}")
    
    def hset(self, name: str, mapping: dict):
        self._data[name] = mapping


redis = MockRedis()


def is_cancelled(job_id: str) -> bool:
    """Check if job has been cancelled."""
    return redis.get(f"job:{job_id}:cancel") is not None


def publish_progress(job_id: str, progress: dict):
    """Publish job progress update."""
    redis.publish(f"job:{job_id}:progress", json.dumps(progress))
    redis.hset(f"job:{job_id}:state", progress)


# =============================================================================
# Main Job Execution Task
# =============================================================================

@app.task(
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True,
)
def execute_skyt_job(
    self,
    job_id: str,
    user_id: str,
    contract_id: str,
    num_runs: int,
    temperature: float,
    model: str,
    restriction_ids: list,
):
    """
    Execute a SKYT pipeline job.
    
    This task:
    1. Loads the contract and restrictions
    2. Generates `num_runs` LLM outputs
    3. Canonicalizes outputs
    4. Computes repeatability metrics
    5. Persists results
    
    Progress is reported via Redis pub/sub for real-time updates.
    
    Args:
        job_id: Job UUID
        user_id: User UUID
        contract_id: Contract identifier
        num_runs: Number of LLM generations
        temperature: Sampling temperature
        model: LLM model identifier
        restriction_ids: List of restriction set UUIDs
    """
    logger.info(f"Starting job {job_id}: {contract_id}, {num_runs} runs @ temp {temperature}")
    
    # Mark job as running
    update_job(UUID(job_id), {
        "status": "generating_outputs",
        "started_at": datetime.utcnow().isoformat(),
        "current_run": 0,
    })
    
    try:
        # Phase 1: Loading contract
        publish_progress(job_id, {
            "phase": "loading_contract",
            "completed_runs": 0,
            "total_runs": num_runs,
        })
        
        # Load contract from database
        contract = get_contract_by_uuid(UUID(contract_id))
        if not contract:
            raise ValueError(f"Contract {contract_id} not found")
        
        prompt = contract.get("prompt", "")
        logger.info(f"Loaded contract: {contract.get('name', contract_id)}")
        
        if is_cancelled(job_id):
            logger.info(f"Job {job_id} cancelled during loading")
            update_job_status(UUID(job_id), "cancelled")
            raise Ignore()
        
        # Initialize LLM client if available
        llm_client = None
        if SKYT_AVAILABLE:
            try:
                llm_client = LLMClient(model=model)
            except Exception as e:
                logger.warning(f"Could not initialize LLM client: {e}")
        
        # Phase 2: Generate outputs
        publish_progress(job_id, {
            "phase": "generating_outputs",
            "completed_runs": 0,
            "total_runs": num_runs,
        })
        
        outputs = []
        raw_codes = []
        
        for i in range(num_runs):
            # Check for cancellation
            if is_cancelled(job_id):
                logger.info(f"Job {job_id} cancelled at run {i}")
                update_job_status(UUID(job_id), "cancelled")
                raise Ignore()
            
            # Report run start
            update_job(UUID(job_id), {"current_run": i, "progress_percent": int((i / num_runs) * 100)})
            publish_progress(job_id, {
                "phase": "generating_outputs",
                "completed_runs": i,
                "total_runs": num_runs,
                "current_run": {"index": i, "status": "in_progress"},
            })
            
            # Generate code
            start_time = time.time()
            
            if llm_client:
                try:
                    raw_code = llm_client.generate(prompt, temperature=temperature)
                except Exception as e:
                    logger.error(f"LLM call failed for run {i}: {e}")
                    raw_code = f"# LLM error: {e}"
            else:
                # Mock generation for testing without LLM
                time.sleep(0.5)
                raw_code = f"def fibonacci(n):\n    # Mock run {i}\n    a, b = 0, 1\n    for _ in range(n):\n        a, b = b, a + b\n    return a"
            
            latency_ms = int((time.time() - start_time) * 1000)
            raw_codes.append(raw_code)
            
            # Save output to database
            output_record = create_job_output(UUID(job_id), {
                "run_number": i,
                "raw_code": raw_code,
                "latency_ms": latency_ms,
            })
            
            outputs.append({
                "run_index": i,
                "raw_output": raw_code,
                "latency_ms": latency_ms,
            })
            
            # Report run completion
            publish_progress(job_id, {
                "phase": "generating_outputs",
                "completed_runs": i + 1,
                "total_runs": num_runs,
            })
        
        # Phase 3: Canonicalization & Oracle testing
        update_job(UUID(job_id), {"status": "canonicalizing", "progress_percent": 80})
        publish_progress(job_id, {"phase": "canonicalizing", "completed_runs": num_runs, "total_runs": num_runs})
        
        canonical_codes = []
        oracle_results = []
        
        if SKYT_AVAILABLE:
            canon_system = CanonSystem()
            oracle_system = OracleSystem()
            transformer = CodeTransformer()
            
            # Get or create canon anchor
            canon_anchor = get_canon_anchor(UUID(contract_id))
            if not canon_anchor and raw_codes:
                # Use first valid output as canon
                canon_system.create_canon(contract_id, raw_codes[0], contract)
                create_canon_anchor(UUID(contract_id), {
                    "canonical_code": raw_codes[0],
                    "canonical_hash": hash(raw_codes[0]),
                })
            
            for i, raw_code in enumerate(raw_codes):
                # Transform to canonical form
                try:
                    canonical = transformer.transform(raw_code, contract)
                    canonical_codes.append(canonical)
                except Exception:
                    canonical_codes.append(raw_code)
                
                # Run oracle tests
                try:
                    oracle_pass = oracle_system.test(canonical_codes[-1], contract)
                    oracle_results.append(oracle_pass)
                except Exception:
                    oracle_results.append(False)
        else:
            canonical_codes = raw_codes.copy()
            oracle_results = [True] * len(raw_codes)
        
        # Phase 4: Compute metrics
        update_job(UUID(job_id), {"status": "computing_metrics", "progress_percent": 90})
        publish_progress(job_id, {"phase": "computing_metrics", "completed_runs": num_runs, "total_runs": num_runs})
        
        # Calculate repeatability metrics
        if SKYT_AVAILABLE:
            metrics_calc = MetricsCalculator()
            metrics = metrics_calc.calculate(raw_codes, canonical_codes, oracle_results, contract_id)
        else:
            # Simple metrics calculation
            unique_raw = len(set(raw_codes))
            unique_canonical = len(set(canonical_codes))
            metrics = {
                "r_raw": (num_runs - unique_raw + 1) / num_runs,
                "r_anchor_pre": 0.0,
                "r_anchor_post": (num_runs - unique_canonical + 1) / num_runs,
                "delta_rescue": 0.0,
                "r_behavioral": sum(oracle_results) / len(oracle_results) if oracle_results else 0.0,
                "r_structural": (num_runs - unique_canonical + 1) / num_runs,
            }
        
        # Save metrics to database
        create_job_metrics(UUID(job_id), metrics)
        
        # Phase 5: Complete
        update_job(UUID(job_id), {
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat(),
            "progress_percent": 100,
        })
        
        publish_progress(job_id, {
            "phase": "completed",
            "completed_runs": num_runs,
            "total_runs": num_runs,
            "metrics": metrics,
        })
        
        logger.info(f"Job {job_id} completed successfully with metrics: {metrics}")
        
        return {
            "job_id": job_id,
            "status": "completed",
            "metrics": metrics,
            "runs_count": len(outputs),
        }
        
    except Ignore:
        raise
    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        update_job(UUID(job_id), {
            "status": "failed",
            "error_message": str(e),
            "completed_at": datetime.utcnow().isoformat(),
        })
        publish_progress(job_id, {"phase": "failed", "error": str(e)})
        raise


@app.task(bind=True)
def execute_skyt_job_high_priority(self, **kwargs):
    """High-priority version of execute_skyt_job for enterprise users."""
    return execute_skyt_job.apply(kwargs=kwargs)


# =============================================================================
# Maintenance Tasks
# =============================================================================

@app.task
def cleanup_old_jobs():
    """
    Clean up old job data.
    
    Runs periodically to:
    - Remove expired results from Redis
    - Archive completed jobs older than retention period
    """
    logger.info("Running job cleanup...")
    # TODO: Implement cleanup logic
    return {"cleaned": 0}


@app.task
def update_job_status(job_id: str, status: str, **kwargs):
    """Update job status in database."""
    logger.info(f"Updating job {job_id} status to {status}")
    # TODO: Update database
    return {"job_id": job_id, "status": status}
