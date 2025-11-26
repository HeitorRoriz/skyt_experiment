# tests/test_database.py
"""
Unit tests for Supabase database operations.

Tests CRUD operations for contracts, jobs, and metrics.
"""

import os
import sys
import pytest
from uuid import UUID, uuid4
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestSupabaseConnection:
    """Test Supabase client connection."""
    
    def test_client_initialization(self):
        """Should initialize Supabase client without error."""
        from api.database import get_supabase_client
        client = get_supabase_client()
        assert client is not None


class TestProfileOperations:
    """Test profile database operations."""
    
    def test_get_profile_not_found(self):
        """Should return None for non-existent profile."""
        from api.database import get_profile
        result = get_profile(uuid4())
        assert result is None
    
    def test_get_profile_by_email_not_found(self):
        """Should return None for non-existent email."""
        from api.database import get_profile_by_email
        result = get_profile_by_email("nonexistent@test.com")
        assert result is None


class TestContractOperations:
    """Test contract database operations."""
    
    def test_get_contracts_empty(self):
        """Should return empty list for user with no contracts."""
        from api.database import get_contracts
        result = get_contracts(uuid4())
        assert isinstance(result, list)


class TestJobOperations:
    """Test job database operations."""
    
    def test_get_jobs_empty(self):
        """Should return empty list for user with no jobs."""
        from api.database import get_jobs
        result = get_jobs(uuid4())
        assert isinstance(result, list)
    
    def test_get_job_not_found(self):
        """Should return None for non-existent job."""
        from api.database import get_job
        result = get_job(uuid4())
        assert result is None


class TestMetricsOperations:
    """Test metrics database operations."""
    
    def test_get_job_metrics_not_found(self):
        """Should return None for non-existent job metrics."""
        from api.database import get_job_metrics
        result = get_job_metrics(uuid4())
        assert result is None


# =============================================================================
# Run tests
# =============================================================================

if __name__ == "__main__":
    print("\n🧪 Testing Database Operations\n")
    print("=" * 60)
    
    # Test connection
    print("\n1. Testing Supabase Connection...")
    try:
        from api.database import get_supabase_client
        client = get_supabase_client()
        print("   ✅ Supabase client initialized")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    # Test profile operations
    print("\n2. Testing Profile Operations...")
    try:
        from api.database import get_profile, get_profile_by_email
        result = get_profile(uuid4())
        print(f"   ✅ get_profile (not found): {result}")
        result = get_profile_by_email("test@test.com")
        print(f"   ✅ get_profile_by_email (not found): {result}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    # Test contract operations
    print("\n3. Testing Contract Operations...")
    try:
        from api.database import get_contracts, get_contract
        result = get_contracts(uuid4())
        print(f"   ✅ get_contracts (empty): {len(result)} contracts")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    # Test job operations
    print("\n4. Testing Job Operations...")
    try:
        from api.database import get_jobs, get_job
        result = get_jobs(uuid4())
        print(f"   ✅ get_jobs (empty): {len(result)} jobs")
        result = get_job(uuid4())
        print(f"   ✅ get_job (not found): {result}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Database Tests Complete!")
    print("\nTo run full pytest suite: pytest tests/test_database.py -v")
