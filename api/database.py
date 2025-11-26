# api/database.py
"""
Supabase database client for SKYT API.

Provides async database operations using Supabase.
"""

import os
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from supabase import create_client, Client


# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://jxzhtejuswyeyerzzmto.supabase.co")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")  # Service role key for backend
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp4emh0ZWp1c3d5ZXllcnp6bXRvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQxNTExMDQsImV4cCI6MjA3OTcyNzEwNH0.pHvCRdLIbL1UoeonupQskMmfdmY68wV18ZuIeXkrejg")


def get_supabase_client() -> Client:
    """Get Supabase client using service key (for backend operations)."""
    key = SUPABASE_SERVICE_KEY or SUPABASE_ANON_KEY
    return create_client(SUPABASE_URL, key)


# =============================================================================
# Profile Operations
# =============================================================================

def get_profile(user_id: UUID) -> Optional[Dict[str, Any]]:
    """Get user profile by ID."""
    client = get_supabase_client()
    response = client.table("profiles").select("*").eq("id", str(user_id)).single().execute()
    return response.data if response.data else None


def get_profile_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user profile by email."""
    client = get_supabase_client()
    response = client.table("profiles").select("*").eq("email", email).single().execute()
    return response.data if response.data else None


def update_profile(user_id: UUID, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update user profile."""
    client = get_supabase_client()
    response = client.table("profiles").update(updates).eq("id", str(user_id)).execute()
    return response.data[0] if response.data else None


def increment_runs(user_id: UUID, count: int = 1) -> None:
    """Increment user's monthly run count."""
    client = get_supabase_client()
    client.rpc("increment_user_runs", {"p_user_id": str(user_id), "p_count": count}).execute()


def check_runs_remaining(user_id: UUID) -> bool:
    """Check if user has runs remaining this month."""
    client = get_supabase_client()
    response = client.rpc("check_runs_remaining", {"p_user_id": str(user_id)}).execute()
    return response.data if response.data else False


# =============================================================================
# Contract Operations
# =============================================================================

def get_contracts(user_id: UUID) -> List[Dict[str, Any]]:
    """Get all contracts for a user."""
    client = get_supabase_client()
    response = client.table("contracts").select("*").eq("user_id", str(user_id)).execute()
    return response.data or []


def get_contract(user_id: UUID, contract_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific contract by contract_id."""
    client = get_supabase_client()
    response = (
        client.table("contracts")
        .select("*")
        .eq("user_id", str(user_id))
        .eq("contract_id", contract_id)
        .single()
        .execute()
    )
    return response.data if response.data else None


def get_contract_by_uuid(contract_uuid: UUID) -> Optional[Dict[str, Any]]:
    """Get a contract by its UUID."""
    client = get_supabase_client()
    response = client.table("contracts").select("*").eq("id", str(contract_uuid)).single().execute()
    return response.data if response.data else None


def create_contract(user_id: UUID, contract_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new contract."""
    client = get_supabase_client()
    contract_data["user_id"] = str(user_id)
    response = client.table("contracts").insert(contract_data).execute()
    return response.data[0] if response.data else {}


def update_contract(contract_uuid: UUID, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update a contract."""
    client = get_supabase_client()
    response = client.table("contracts").update(updates).eq("id", str(contract_uuid)).execute()
    return response.data[0] if response.data else None


def delete_contract(contract_uuid: UUID) -> bool:
    """Delete a contract."""
    client = get_supabase_client()
    response = client.table("contracts").delete().eq("id", str(contract_uuid)).execute()
    return bool(response.data)


# =============================================================================
# Job Operations
# =============================================================================

def get_jobs(user_id: UUID, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    """Get jobs for a user."""
    client = get_supabase_client()
    response = (
        client.table("jobs")
        .select("*, contracts(name, contract_id)")
        .eq("user_id", str(user_id))
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )
    return response.data or []


def get_job(job_id: UUID) -> Optional[Dict[str, Any]]:
    """Get a job by ID."""
    client = get_supabase_client()
    response = (
        client.table("jobs")
        .select("*, contracts(name, contract_id, prompt)")
        .eq("id", str(job_id))
        .single()
        .execute()
    )
    return response.data if response.data else None


def create_job(user_id: UUID, contract_uuid: UUID, config: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new job."""
    client = get_supabase_client()
    job_data = {
        "user_id": str(user_id),
        "contract_id": str(contract_uuid),
        "num_runs": config.get("num_runs", 10),
        "temperature": config.get("temperature", 0.3),
        "model": config.get("model", "gpt-4o-mini"),
        "status": "queued",
    }
    response = client.table("jobs").insert(job_data).execute()
    return response.data[0] if response.data else {}


def update_job(job_id: UUID, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update job status/progress."""
    client = get_supabase_client()
    response = client.table("jobs").update(updates).eq("id", str(job_id)).execute()
    return response.data[0] if response.data else None


def update_job_status(job_id: UUID, status: str, **kwargs) -> None:
    """Update job status with optional additional fields."""
    updates = {"status": status, **kwargs}
    if status == "completed":
        updates["completed_at"] = datetime.utcnow().isoformat()
    update_job(job_id, updates)


# =============================================================================
# Job Output Operations
# =============================================================================

def create_job_output(job_id: UUID, output_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a job output record."""
    client = get_supabase_client()
    output_data["job_id"] = str(job_id)
    response = client.table("job_outputs").insert(output_data).execute()
    return response.data[0] if response.data else {}


def get_job_outputs(job_id: UUID) -> List[Dict[str, Any]]:
    """Get all outputs for a job."""
    client = get_supabase_client()
    response = (
        client.table("job_outputs")
        .select("*")
        .eq("job_id", str(job_id))
        .order("run_number")
        .execute()
    )
    return response.data or []


# =============================================================================
# Job Metrics Operations
# =============================================================================

def create_job_metrics(job_id: UUID, metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Create job metrics record."""
    client = get_supabase_client()
    metrics["job_id"] = str(job_id)
    response = client.table("job_metrics").insert(metrics).execute()
    return response.data[0] if response.data else {}


def get_job_metrics(job_id: UUID) -> Optional[Dict[str, Any]]:
    """Get metrics for a job."""
    client = get_supabase_client()
    response = client.table("job_metrics").select("*").eq("job_id", str(job_id)).single().execute()
    return response.data if response.data else None


# =============================================================================
# Canon Anchor Operations
# =============================================================================

def get_canon_anchor(contract_uuid: UUID) -> Optional[Dict[str, Any]]:
    """Get canonical anchor for a contract."""
    client = get_supabase_client()
    response = (
        client.table("canon_anchors")
        .select("*")
        .eq("contract_id", str(contract_uuid))
        .single()
        .execute()
    )
    return response.data if response.data else None


def create_canon_anchor(contract_uuid: UUID, anchor_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create or update canonical anchor."""
    client = get_supabase_client()
    anchor_data["contract_id"] = str(contract_uuid)
    
    # Upsert: update if exists, insert if not
    response = (
        client.table("canon_anchors")
        .upsert(anchor_data, on_conflict="contract_id")
        .execute()
    )
    return response.data[0] if response.data else {}
