# tests/test_full_stack.py
"""
Full Stack Integration Tests for SKYT SaaS

Tests the complete flow from API to Workers to Core Engine.
Uses FastAPI TestClient and mocked dependencies.

Run with:
    pytest tests/test_full_stack.py -v
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
def test_client():
    """Create FastAPI test client."""
    from fastapi.testclient import TestClient
    from api.main import app
    return TestClient(app)


@pytest.fixture
def mock_supabase():
    """Mock Supabase client for isolated testing."""
    with patch('api.database.get_supabase_client') as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


# =============================================================================
# API Health Tests
# =============================================================================

class TestAPIHealth:
    """Test API health endpoints."""
    
    def test_health_endpoint(self, test_client):
        """Health endpoint should return 200."""
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_ready_endpoint(self, test_client):
        """Ready endpoint should return 200."""
        response = test_client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert "ready" in data


# =============================================================================
# API Route Tests
# =============================================================================

class TestAPIRoutes:
    """Test API routes exist and respond correctly."""
    
    def test_docs_available(self, test_client):
        """OpenAPI docs should be available."""
        response = test_client.get("/docs")
        assert response.status_code == 200
    
    def test_openapi_schema(self, test_client):
        """OpenAPI schema should be valid."""
        response = test_client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "paths" in schema
        assert "/api/v1/pipeline/run" in schema["paths"]
    
    def test_auth_me_requires_auth(self, test_client):
        """Auth endpoint should require authentication."""
        response = test_client.get("/api/v1/auth/me")
        assert response.status_code == 401
    
    def test_pipeline_run_requires_auth(self, test_client):
        """Pipeline run should require authentication."""
        response = test_client.post("/api/v1/pipeline/run", json={
            "contract_id": "test",
            "num_runs": 5
        })
        assert response.status_code == 401


# =============================================================================
# Core Engine Import Tests
# =============================================================================

class TestCoreEngineImports:
    """Test that core engine modules can be imported."""
    
    def test_import_llm_client(self):
        """LLMClient should be importable."""
        from src.llm_client import LLMClient
        assert LLMClient is not None
    
    def test_import_metrics(self):
        """Metrics module should be importable."""
        from src.metrics import ComprehensiveMetrics
        assert ComprehensiveMetrics is not None
    
    def test_import_canon_system(self):
        """CanonSystem should be importable."""
        from src.canon_system import CanonSystem
        assert CanonSystem is not None
    
    def test_import_oracle_system(self):
        """OracleSystem should be importable."""
        from src.oracle_system import OracleSystem
        assert OracleSystem is not None
    
    def test_import_code_transformer(self):
        """CodeTransformer should be importable."""
        from src.code_transformer import CodeTransformer
        assert CodeTransformer is not None


# =============================================================================
# Worker Import Tests
# =============================================================================

class TestWorkerImports:
    """Test that worker modules can be imported."""
    
    def test_import_celery_app(self):
        """Celery app should be importable."""
        from workers.celery_app import app
        assert app is not None
        assert app.main == "skyt_workers"
    
    def test_import_tasks(self):
        """Tasks should be importable."""
        from workers.tasks import execute_skyt_job
        assert execute_skyt_job is not None
    
    def test_task_registered(self):
        """Task should be registered with Celery."""
        from workers.celery_app import app
        from workers.tasks import execute_skyt_job
        assert execute_skyt_job.name in app.tasks


# =============================================================================
# Database Client Tests
# =============================================================================

class TestDatabaseClient:
    """Test database client functions."""
    
    def test_get_supabase_client(self):
        """Should create Supabase client."""
        from api.database import get_supabase_client
        client = get_supabase_client()
        assert client is not None
    
    def test_database_functions_exist(self):
        """All required database functions should exist."""
        from api import database
        
        required_functions = [
            'get_profile',
            'get_profile_by_email',
            'get_contracts',
            'get_contract',
            'create_contract',
            'get_jobs',
            'get_job',
            'create_job',
            'update_job',
            'create_job_output',
            'create_job_metrics',
            'get_canon_anchor',
            'create_canon_anchor',
        ]
        
        for func_name in required_functions:
            assert hasattr(database, func_name), f"Missing function: {func_name}"


# =============================================================================
# Core Interfaces Tests
# =============================================================================

class TestCoreInterfaces:
    """Test core interface definitions."""
    
    def test_interfaces_module_exists(self):
        """Core interfaces module should exist."""
        from src.core import interfaces
        assert interfaces is not None
    
    def test_models_module_exists(self):
        """Core models module should exist."""
        from src.core import models
        assert models is not None
    
    def test_observable_llm_exists(self):
        """Observable LLM wrapper should exist."""
        from src.core.observable_llm import ObservableLLMClient
        assert ObservableLLMClient is not None


# =============================================================================
# Contract Templates Tests
# =============================================================================

class TestContractTemplates:
    """Test contract templates are valid."""
    
    def test_templates_file_exists(self):
        """Templates file should exist."""
        import json
        templates_path = os.path.join(PROJECT_ROOT, "contracts", "templates.json")
        assert os.path.exists(templates_path)
        
        with open(templates_path) as f:
            templates = json.load(f)
        
        assert len(templates) > 0
    
    def test_templates_have_required_fields(self):
        """Each template should have required fields."""
        import json
        templates_path = os.path.join(PROJECT_ROOT, "contracts", "templates.json")
        
        with open(templates_path) as f:
            templates = json.load(f)
        
        # Top-level required fields
        required_fields = ["prompt", "oracle_requirements", "constraints"]
        
        for contract_id, template in templates.items():
            for field in required_fields:
                assert field in template, f"Contract {contract_id} missing {field}"
            
            # Must have either function_name or class_name in constraints
            constraints = template.get("constraints", {})
            has_name = "function_name" in constraints or "class_name" in constraints
            assert has_name, \
                f"Contract {contract_id} missing constraints.function_name or constraints.class_name"


# =============================================================================
# SKYT Contracts Repository Tests
# =============================================================================

class TestSKYTContractsRepo:
    """Test skyt-contracts repository structure."""
    
    def test_contracts_dir_exists(self):
        """skyt-contracts directory should exist."""
        contracts_dir = os.path.join(PROJECT_ROOT, "skyt-contracts")
        assert os.path.isdir(contracts_dir)
    
    def test_schema_dir_exists(self):
        """Schema directory should exist."""
        schema_dir = os.path.join(PROJECT_ROOT, "skyt-contracts", "schema")
        assert os.path.isdir(schema_dir)
    
    def test_restrictions_dir_exists(self):
        """Restrictions directory should exist."""
        restrictions_dir = os.path.join(PROJECT_ROOT, "skyt-contracts", "restrictions")
        assert os.path.isdir(restrictions_dir)


# =============================================================================
# End-to-End Workflow Test (Mocked)
# =============================================================================

class TestEndToEndWorkflow:
    """Test complete workflow with mocked dependencies."""
    
    def test_job_execution_flow(self):
        """Test complete job execution with mocks."""
        from workers.celery_app import app
        from workers.tasks import execute_skyt_job
        
        # Enable eager mode
        app.conf.update(task_always_eager=True, task_eager_propagates=True)
        
        try:
            with patch('workers.tasks.get_contract_by_uuid') as mock_get, \
                 patch('workers.tasks.update_job'), \
                 patch('workers.tasks.create_job_output') as mock_output, \
                 patch('workers.tasks.create_job_metrics'), \
                 patch('workers.tasks.get_canon_anchor') as mock_canon, \
                 patch('workers.tasks.create_canon_anchor'):
                
                mock_get.return_value = {
                    "id": str(uuid4()),
                    "name": "fibonacci_basic",
                    "prompt": "Write a Python function called 'fibonacci' that returns the nth Fibonacci number using iteration.",
                }
                mock_output.return_value = {"id": str(uuid4())}
                mock_canon.return_value = None
                
                result = execute_skyt_job(
                    job_id=str(uuid4()),
                    user_id=str(uuid4()),
                    contract_id=str(uuid4()),
                    num_runs=5,
                    temperature=0.3,
                    model="gpt-4o-mini",
                    restriction_ids=[],
                )
                
                # Verify result
                assert result["status"] == "completed"
                assert result["runs_count"] == 5
                assert "metrics" in result
                assert "r_raw" in result["metrics"]
                assert "r_behavioral" in result["metrics"]
        finally:
            # Reset eager mode
            app.conf.update(task_always_eager=False, task_eager_propagates=False)


# =============================================================================
# Summary Report
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🧪 SKYT Full Stack Tests")
    print("=" * 70)
    
    # Quick import checks
    print("\n1. Checking imports...")
    
    checks = [
        ("API", "from api.main import app"),
        ("Database", "from api.database import get_supabase_client"),
        ("Celery", "from workers.celery_app import app"),
        ("Tasks", "from workers.tasks import execute_skyt_job"),
        ("LLM Client", "from src.llm_client import LLMClient"),
        ("Metrics", "from src.metrics import ComprehensiveMetrics"),
        ("Canon System", "from src.canon_system import CanonSystem"),
        ("Oracle System", "from src.oracle_system import OracleSystem"),
        ("Code Transformer", "from src.code_transformer import CodeTransformer"),
    ]
    
    all_passed = True
    for name, import_stmt in checks:
        try:
            exec(import_stmt)
            print(f"   ✅ {name}")
        except Exception as e:
            print(f"   ❌ {name}: {e}")
            all_passed = False
    
    print("\n2. Checking file structure...")
    required_files = [
        "api/main.py",
        "api/database.py",
        "workers/celery_app.py",
        "workers/tasks.py",
        "contracts/templates.json",
        "skyt-contracts/schema/contract.schema.json",
    ]
    
    for file_path in required_files:
        full_path = os.path.join(PROJECT_ROOT, file_path)
        if os.path.exists(full_path):
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} NOT FOUND")
            all_passed = False
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ All checks passed!")
    else:
        print("❌ Some checks failed")
    print("=" * 70)
    print("\nTo run full pytest suite:")
    print("  pytest tests/test_full_stack.py -v")
