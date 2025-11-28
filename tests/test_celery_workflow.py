# tests/test_celery_workflow.py
"""
Simple unit test for Celery workflow.

Tests the SKYT job execution flow without requiring a real Redis/Celery setup.
Uses Celery's eager mode to execute tasks synchronously.

Run with:
    pytest tests/test_celery_workflow.py -v
    
Or directly:
    python tests/test_celery_workflow.py
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def celery_eager():
    """Configure Celery to run tasks synchronously (eager mode)."""
    from workers.celery_app import app
    app.conf.update(
        task_always_eager=True,
        task_eager_propagates=True,
    )
    yield app
    # Reset after test
    app.conf.update(
        task_always_eager=False,
        task_eager_propagates=False,
    )


@pytest.fixture
def mock_database():
    """Mock all database operations."""
    with patch('workers.tasks.get_contract_by_uuid') as mock_get_contract, \
         patch('workers.tasks.update_job') as mock_update_job, \
         patch('workers.tasks.update_job_status') as mock_update_status, \
         patch('workers.tasks.create_job_output') as mock_create_output, \
         patch('workers.tasks.create_job_metrics') as mock_create_metrics, \
         patch('workers.tasks.get_canon_anchor') as mock_get_canon, \
         patch('workers.tasks.create_canon_anchor') as mock_create_canon:
        
        # Configure mocks
        mock_get_contract.return_value = {
            "id": str(uuid4()),
            "name": "fibonacci_test",
            "prompt": "Write a Python function called 'fibonacci' that returns the nth Fibonacci number.",
        }
        mock_update_job.return_value = {}
        mock_update_status.return_value = {}
        mock_create_output.return_value = {"id": str(uuid4())}
        mock_create_metrics.return_value = {"id": str(uuid4())}
        mock_get_canon.return_value = None
        mock_create_canon.return_value = {"id": str(uuid4())}
        
        yield {
            "get_contract": mock_get_contract,
            "update_job": mock_update_job,
            "update_status": mock_update_status,
            "create_output": mock_create_output,
            "create_metrics": mock_create_metrics,
            "get_canon": mock_get_canon,
            "create_canon": mock_create_canon,
        }


# =============================================================================
# Tests
# =============================================================================

class TestCeleryWorkflow:
    """Test the complete Celery job execution workflow."""
    
    def test_job_executes_with_mock_llm(self, celery_eager, mock_database):
        """
        Test that a job executes successfully with mocked dependencies.
        
        This tests the complete workflow:
        1. Load contract
        2. Generate outputs (mocked)
        3. Compute metrics
        4. Return results
        """
        from workers.tasks import execute_skyt_job
        
        # Execute job
        job_id = str(uuid4())
        result = execute_skyt_job(
            job_id=job_id,
            user_id=str(uuid4()),
            contract_id=str(uuid4()),
            num_runs=3,
            temperature=0.5,
            model="gpt-4o-mini",
            restriction_ids=[],
        )
        
        # Verify result structure
        assert result is not None
        assert result["status"] == "completed"
        assert result["job_id"] == job_id
        assert result["runs_count"] == 3
        assert "metrics" in result
        
        # Verify metrics structure
        metrics = result["metrics"]
        assert "r_raw" in metrics
        assert "r_behavioral" in metrics
        assert 0.0 <= metrics["r_raw"] <= 1.0
        assert 0.0 <= metrics["r_behavioral"] <= 1.0
    
    def test_job_creates_outputs(self, celery_eager, mock_database):
        """Test that job creates the correct number of outputs."""
        from workers.tasks import execute_skyt_job
        
        num_runs = 5
        execute_skyt_job(
            job_id=str(uuid4()),
            user_id=str(uuid4()),
            contract_id=str(uuid4()),
            num_runs=num_runs,
            temperature=0.3,
            model="gpt-4o-mini",
            restriction_ids=[],
        )
        
        # Verify create_job_output was called for each run
        assert mock_database["create_output"].call_count == num_runs
    
    def test_job_updates_progress(self, celery_eager, mock_database):
        """Test that job updates progress correctly."""
        from workers.tasks import execute_skyt_job
        
        execute_skyt_job(
            job_id=str(uuid4()),
            user_id=str(uuid4()),
            contract_id=str(uuid4()),
            num_runs=2,
            temperature=0.5,
            model="gpt-4o-mini",
            restriction_ids=[],
        )
        
        # Verify update_job was called multiple times (phases)
        assert mock_database["update_job"].call_count >= 4  # initial + runs + canonicalize + metrics + complete
    
    def test_job_handles_missing_contract(self, celery_eager, mock_database):
        """Test that job fails gracefully when contract not found."""
        from workers.tasks import execute_skyt_job
        
        # Make contract lookup return None
        mock_database["get_contract"].return_value = None
        
        with pytest.raises(ValueError, match="not found"):
            execute_skyt_job(
                job_id=str(uuid4()),
                user_id=str(uuid4()),
                contract_id=str(uuid4()),
                num_runs=1,
                temperature=0.5,
                model="gpt-4o-mini",
                restriction_ids=[],
            )
    
    def test_metrics_calculation(self, celery_eager, mock_database):
        """Test that metrics are calculated and saved."""
        from workers.tasks import execute_skyt_job
        
        result = execute_skyt_job(
            job_id=str(uuid4()),
            user_id=str(uuid4()),
            contract_id=str(uuid4()),
            num_runs=3,
            temperature=0.5,
            model="gpt-4o-mini",
            restriction_ids=[],
        )
        
        # Metrics should be created
        assert mock_database["create_metrics"].called
        
        # Result should contain metrics
        metrics = result["metrics"]
        
        # With mock (identical outputs), repeatability should be high
        assert metrics["r_raw"] >= 0.3  # At least some repeatability expected
        assert metrics["r_behavioral"] == 1.0  # All mocks pass oracle


class TestProgressHelpers:
    """Test progress reporting utilities."""
    
    def test_is_cancelled_returns_false_for_new_job(self):
        """New jobs should not be cancelled."""
        from workers.tasks import is_cancelled
        
        assert is_cancelled(str(uuid4())) is False
    
    def test_publish_progress_does_not_raise(self):
        """Progress publishing should not raise errors."""
        from workers.tasks import publish_progress
        
        # Should execute without error
        publish_progress(str(uuid4()), {
            "phase": "test",
            "completed_runs": 0,
            "total_runs": 5,
        })


class TestTaskConfiguration:
    """Test task configuration and registration."""
    
    def test_execute_skyt_job_has_retry_config(self):
        """Task should have retry configuration."""
        from workers.tasks import execute_skyt_job
        
        assert hasattr(execute_skyt_job, 'max_retries')
        # Default is 3 from decorator
    
    def test_task_is_registered(self):
        """Task should be registered with Celery app."""
        from workers.celery_app import app
        from workers.tasks import execute_skyt_job
        
        assert execute_skyt_job.name in app.tasks


# =============================================================================
# Integration Test (Optional - requires Redis)
# =============================================================================

class TestCeleryIntegration:
    """
    Integration tests that require a running Redis instance.
    
    Skip these if Redis is not available.
    """
    
    @pytest.mark.skipif(
        os.getenv("SKIP_INTEGRATION", "1") == "1",
        reason="Integration tests disabled. Set SKIP_INTEGRATION=0 to run."
    )
    def test_async_job_execution(self, mock_database):
        """Test async job execution with real Celery."""
        from workers.tasks import execute_skyt_job
        
        # Send task to queue
        result = execute_skyt_job.delay(
            job_id=str(uuid4()),
            user_id=str(uuid4()),
            contract_id=str(uuid4()),
            num_runs=2,
            temperature=0.5,
            model="gpt-4o-mini",
            restriction_ids=[],
        )
        
        # Wait for result (timeout 30s)
        job_result = result.get(timeout=30)
        
        assert job_result["status"] == "completed"


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🧪 SKYT Celery Workflow Tests")
    print("=" * 70)
    
    # Quick sanity checks without pytest
    print("\n1. Testing imports...")
    try:
        from workers.celery_app import app
        from workers.tasks import execute_skyt_job, is_cancelled, publish_progress
        print("   ✅ All imports successful")
    except ImportError as e:
        print(f"   ❌ Import failed: {e}")
        sys.exit(1)
    
    print("\n2. Testing Celery app configuration...")
    print(f"   ✅ App name: {app.main}")
    print(f"   ✅ Broker: {app.conf.broker_url}")
    print(f"   ✅ Task routes: {list(app.conf.task_routes.keys())}")
    
    print("\n3. Testing task registration...")
    print(f"   ✅ execute_skyt_job: {execute_skyt_job.name}")
    print(f"   ✅ Task bound: {execute_skyt_job.bind}")
    
    print("\n4. Testing helper functions...")
    assert is_cancelled("test-id") is False
    print("   ✅ is_cancelled works")
    publish_progress("test-id", {"phase": "test"})
    print("   ✅ publish_progress works")
    
    print("\n5. Testing eager execution...")
    # Enable eager mode
    app.conf.update(task_always_eager=True, task_eager_propagates=True)
    
    # Mock database calls
    with patch('workers.tasks.get_contract_by_uuid') as mock_get, \
         patch('workers.tasks.update_job'), \
         patch('workers.tasks.create_job_output') as mock_output, \
         patch('workers.tasks.create_job_metrics'), \
         patch('workers.tasks.get_canon_anchor') as mock_canon, \
         patch('workers.tasks.create_canon_anchor'):
        
        mock_get.return_value = {
            "id": str(uuid4()),
            "name": "test_contract",
            "prompt": "Write a fibonacci function",
        }
        mock_output.return_value = {"id": str(uuid4())}
        mock_canon.return_value = None
        
        result = execute_skyt_job(
            job_id=str(uuid4()),
            user_id=str(uuid4()),
            contract_id=str(uuid4()),
            num_runs=3,
            temperature=0.5,
            model="test",
            restriction_ids=[],
        )
        
        print(f"   ✅ Job completed: {result['status']}")
        print(f"   ✅ Runs executed: {result['runs_count']}")
        print(f"   ✅ Metrics: R_raw={result['metrics']['r_raw']:.2f}, R_behavioral={result['metrics']['r_behavioral']:.2f}")
    
    print("\n" + "=" * 70)
    print("✅ All sanity checks passed!")
    print("=" * 70)
    print("\nTo run full pytest suite:")
    print("  pytest tests/test_celery_workflow.py -v")
    print("\nTo run integration tests (requires Redis):")
    print("  SKIP_INTEGRATION=0 pytest tests/test_celery_workflow.py -v")
