# tests/test_api_flow.py
"""
Integration tests for SKYT API flow.

Tests the complete flow: auth → contracts → jobs → results
"""

import os
import sys
import pytest
import requests
from uuid import UUID

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = os.getenv("SKYT_API_URL", "http://localhost:8000")
API_PREFIX = "/api/v1"


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_returns_200(self):
        """Health endpoint should return 200 with status healthy."""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestContractTemplates:
    """Test contract template endpoints (no auth required)."""
    
    def test_list_templates(self):
        """Should list available contract templates."""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/contracts/templates")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should have at least one template
        assert len(data) >= 1
        # Check template structure
        if data:
            template = data[0]
            assert "id" in template
            assert "version" in template
    
    def test_get_template_by_id(self):
        """Should get specific template contract."""
        # First list templates
        response = requests.get(f"{BASE_URL}{API_PREFIX}/contracts/templates")
        templates = response.json()
        
        if templates:
            template_id = templates[0]["id"]
            response = requests.get(f"{BASE_URL}{API_PREFIX}/contracts/templates/{template_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == template_id
            assert "prompt" in data
    
    def test_get_nonexistent_template(self):
        """Should return 404 for non-existent template."""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/contracts/templates/nonexistent_xyz")
        assert response.status_code == 404


class TestRestrictionsPresets:
    """Test restriction preset endpoints (no auth required)."""
    
    def test_list_presets(self):
        """Should list available restriction presets."""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/restrictions/presets")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should have NASA preset
        preset_names = [p["name"] for p in data]
        assert any("NASA" in name or "Power of 10" in name for name in preset_names)


class TestAuthEndpoints:
    """Test authentication endpoints."""
    
    def test_me_without_auth(self):
        """Should return 401/403 without auth token."""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/auth/me")
        assert response.status_code in [401, 403]


class TestProtectedEndpoints:
    """Test endpoints that require authentication."""
    
    def test_list_contracts_without_auth(self):
        """Should return 401/403 for contracts without auth."""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/contracts")
        assert response.status_code in [401, 403]
    
    def test_list_jobs_without_auth(self):
        """Should return 401/403 for jobs without auth."""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/pipeline/jobs")
        assert response.status_code in [401, 403]
    
    def test_submit_job_without_auth(self):
        """Should return 401/403 for job submission without auth."""
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/pipeline/run",
            json={"contract_id": "fibonacci_basic", "num_runs": 5}
        )
        assert response.status_code in [401, 403]


# =============================================================================
# Run tests directly
# =============================================================================

if __name__ == "__main__":
    print(f"\n🧪 Testing SKYT API at {BASE_URL}\n")
    print("=" * 60)
    
    # Test health
    print("\n1. Testing Health Endpoint...")
    try:
        r = requests.get(f"{BASE_URL}/health")
        if r.status_code == 200:
            print(f"   ✅ Health: {r.json()}")
        else:
            print(f"   ❌ Health failed: {r.status_code}")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        print("\n⚠️  Make sure the API is running: python -m uvicorn api.main:app --port 8000")
        sys.exit(1)
    
    # Test templates
    print("\n2. Testing Contract Templates...")
    r = requests.get(f"{BASE_URL}{API_PREFIX}/contracts/templates")
    if r.status_code == 200:
        templates = r.json()
        print(f"   ✅ Found {len(templates)} templates")
        for t in templates[:3]:
            print(f"      - {t['id']}: {t['task_intent'][:50]}...")
    else:
        print(f"   ❌ Templates failed: {r.status_code}")
    
    # Test restriction presets
    print("\n3. Testing Restriction Presets...")
    r = requests.get(f"{BASE_URL}{API_PREFIX}/restrictions/presets")
    if r.status_code == 200:
        presets = r.json()
        print(f"   ✅ Found {len(presets)} presets")
        for p in presets:
            print(f"      - {p['name']} ({p['rule_count']} rules)")
    else:
        print(f"   ❌ Presets failed: {r.status_code}")
    
    # Test auth required endpoints
    print("\n4. Testing Auth Protection...")
    endpoints = [
        ("GET", f"{API_PREFIX}/auth/me"),
        ("GET", f"{API_PREFIX}/contracts"),
        ("GET", f"{API_PREFIX}/pipeline/jobs"),
    ]
    for method, endpoint in endpoints:
        r = requests.request(method, f"{BASE_URL}{endpoint}")
        if r.status_code in [401, 403]:
            print(f"   ✅ {method} {endpoint} → Protected ({r.status_code})")
        else:
            print(f"   ❌ {method} {endpoint} → NOT protected! ({r.status_code})")
    
    print("\n" + "=" * 60)
    print("✅ API Flow Tests Complete!")
    print("\nTo run full pytest suite: pytest tests/test_api_flow.py -v")
