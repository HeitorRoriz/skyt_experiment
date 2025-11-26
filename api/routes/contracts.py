# api/routes/contracts.py
"""
Contract and restriction endpoints.

Browse available contracts and manage restriction sets.
Integrates with Supabase for user contracts.
"""

import json
from pathlib import Path
from typing import Optional, List
from uuid import UUID, uuid4
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from .auth import get_current_user, User
from ..database import (
    get_contracts as db_get_contracts,
    get_contract as db_get_contract,
    create_contract as db_create_contract,
    update_contract as db_update_contract,
    delete_contract as db_delete_contract,
)


router = APIRouter()


# Path to template contracts
TEMPLATES_PATH = Path(__file__).parent.parent.parent / "contracts" / "templates.json"


# =============================================================================
# Response Models
# =============================================================================

class ContractSummary(BaseModel):
    """Brief contract information for listings."""
    id: str
    version: str
    task_intent: str
    algorithm_family: str
    test_count: int


class ContractDetail(BaseModel):
    """Full contract details."""
    id: str
    version: str
    task_intent: str
    prompt: str
    description: Optional[str]
    algorithm_family: str
    constraints: dict
    oracle_requirements: dict
    rescue_bounds: dict


class RestrictionSummary(BaseModel):
    """Brief restriction set information."""
    id: UUID
    name: str
    version: str
    source: str  # preset, user, community
    authority: Optional[str]
    rule_count: int


class RestrictionDetail(BaseModel):
    """Full restriction set details."""
    id: UUID
    name: str
    version: str
    source: str
    authority: Optional[str]
    description: Optional[str]
    applicable_languages: List[str]
    rules: List[dict]


# =============================================================================
# Template Contracts (from filesystem)
# =============================================================================

def load_template_contracts() -> dict:
    """Load template contracts from templates.json file."""
    try:
        if TEMPLATES_PATH.exists():
            with open(TEMPLATES_PATH) as f:
                data = json.load(f)
                return {c["id"]: c for c in data.get("contracts", [])}
    except Exception:
        pass
    
    # Fallback to minimal set if file not found
    return {
        "fibonacci_basic": {
            "id": "fibonacci_basic",
            "version": "1.0.0",
            "task_intent": "Generate nth Fibonacci number using iteration",
            "prompt": "Write a Python function called 'fibonacci' that takes an integer n and returns the nth Fibonacci number. Use iteration, not recursion.",
            "description": "Basic iterative Fibonacci implementation",
            "algorithm_family": "fibonacci",
            "constraints": {"function_name": "fibonacci", "implementation_style": "iterative"},
            "oracle_requirements": {"test_cases": [{"input": 0, "expected": 0}, {"input": 10, "expected": 55}]},
            "rescue_bounds": {"max_transformations": 5},
        },
    }


# Cache template contracts
_template_contracts = None

def get_template_contracts() -> dict:
    """Get cached template contracts."""
    global _template_contracts
    if _template_contracts is None:
        _template_contracts = load_template_contracts()
    return _template_contracts

_mock_restrictions = {
    "nasa_power_of_10": {
        "id": uuid4(),
        "name": "NASA/JPL Power of 10 Rules",
        "version": "1.0.0",
        "source": "preset",
        "authority": "NASA/JPL Laboratory for Reliable Software",
        "description": "Ten rules for writing safety-critical code",
        "applicable_languages": ["c", "cpp", "python"],
        "rules": [
            {"id": "P10-R1", "name": "Simple Control Flow", "severity": "mandatory"},
            {"id": "P10-R2", "name": "Fixed Loop Bounds", "severity": "mandatory"},
            {"id": "P10-R3", "name": "No Dynamic Memory After Init", "severity": "mandatory"},
            {"id": "P10-R4", "name": "Short Functions", "severity": "required"},
            {"id": "P10-R5", "name": "Low Assertion Density", "severity": "required"},
            {"id": "P10-R6", "name": "Minimal Variable Scope", "severity": "required"},
            {"id": "P10-R7", "name": "Check Return Values", "severity": "mandatory"},
            {"id": "P10-R8", "name": "Limited Preprocessor Use", "severity": "mandatory"},
            {"id": "P10-R9", "name": "Limited Pointer Use", "severity": "mandatory"},
            {"id": "P10-R10", "name": "Compile with All Warnings", "severity": "mandatory"},
        ],
    },
}


# =============================================================================
# Contract Endpoints
# =============================================================================

@router.get("/contracts/templates", response_model=List[ContractSummary])
async def list_template_contracts(
    algorithm_family: Optional[str] = None,
):
    """
    List available template contracts (public, no auth required).
    
    Templates are pre-built contracts for common algorithms.
    """
    contracts = list(get_template_contracts().values())
    
    if algorithm_family:
        contracts = [c for c in contracts if c.get("algorithm_family") == algorithm_family]
    
    return [
        ContractSummary(
            id=c["id"],
            version=c.get("version", "1.0.0"),
            task_intent=c.get("task_intent", c.get("description", "")),
            algorithm_family=c.get("algorithm_family", "general"),
            test_count=len(c.get("oracle_requirements", {}).get("test_cases", [])),
        )
        for c in contracts
    ]


@router.get("/contracts/templates/{contract_id}", response_model=ContractDetail)
async def get_template_contract(contract_id: str):
    """
    Get template contract details (public, no auth required).
    """
    contract = get_template_contracts().get(contract_id)
    
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template contract '{contract_id}' not found",
        )
    
    return ContractDetail(
        id=contract["id"],
        version=contract.get("version", "1.0.0"),
        task_intent=contract.get("task_intent", contract.get("description", "")),
        prompt=contract.get("prompt", ""),
        description=contract.get("description"),
        algorithm_family=contract.get("algorithm_family", "general"),
        constraints=contract.get("constraints", {}),
        oracle_requirements=contract.get("oracle_requirements", {}),
        rescue_bounds=contract.get("rescue_bounds", {}),
    )


@router.get("/contracts", response_model=List[ContractSummary])
async def list_user_contracts(
    user: User = Depends(get_current_user),
):
    """
    List user's contracts.
    
    Returns contracts created/owned by the authenticated user.
    """
    contracts = db_get_contracts(user.id)
    
    return [
        ContractSummary(
            id=c["contract_id"],
            version=c.get("version", "1.0.0"),
            task_intent=c.get("description", c.get("name", "")),
            algorithm_family=c.get("constraints", {}).get("algorithm_family", "custom"),
            test_count=len(c.get("oracle_requirements", {}).get("test_cases", [])),
        )
        for c in contracts
    ]


class ContractCreate(BaseModel):
    """Request body for creating a contract."""
    contract_id: str
    name: str
    description: Optional[str] = None
    prompt: str
    constraints: dict = {}
    oracle_requirements: dict = {}
    variable_naming: dict = {}
    restriction_preset: Optional[str] = None
    from_template: Optional[str] = None  # Copy from template


@router.post("/contracts", status_code=status.HTTP_201_CREATED)
async def create_contract(
    contract_data: ContractCreate,
    user: User = Depends(get_current_user),
):
    """
    Create a new contract.
    
    Optionally copy from a template using `from_template`.
    """
    # Check if contract_id already exists for this user
    existing = db_get_contract(user.id, contract_data.contract_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Contract '{contract_data.contract_id}' already exists",
        )
    
    # If from_template, copy template data
    base_data = {}
    if contract_data.from_template:
        template = get_template_contracts().get(contract_data.from_template)
        if template:
            base_data = {
                "prompt": template.get("prompt", ""),
                "constraints": template.get("constraints", {}),
                "oracle_requirements": template.get("oracle_requirements", {}),
                "variable_naming": template.get("variable_naming", {}),
            }
    
    # Merge with provided data (provided data takes precedence)
    create_data = {
        **base_data,
        "contract_id": contract_data.contract_id,
        "name": contract_data.name,
        "description": contract_data.description,
        "prompt": contract_data.prompt or base_data.get("prompt", ""),
        "constraints": contract_data.constraints or base_data.get("constraints", {}),
        "oracle_requirements": contract_data.oracle_requirements or base_data.get("oracle_requirements", {}),
        "variable_naming": contract_data.variable_naming or base_data.get("variable_naming", {}),
        "restriction_preset": contract_data.restriction_preset,
    }
    
    result = db_create_contract(user.id, create_data)
    return {"id": result.get("id"), "contract_id": result.get("contract_id"), "message": "Contract created"}


@router.get("/contracts/{contract_id}")
async def get_user_contract(
    contract_id: str,
    user: User = Depends(get_current_user),
):
    """
    Get a user's contract by contract_id.
    """
    contract = db_get_contract(user.id, contract_id)
    
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract '{contract_id}' not found",
        )
    
    return contract


@router.delete("/contracts/{contract_id}")
async def delete_user_contract(
    contract_id: str,
    user: User = Depends(get_current_user),
):
    """
    Delete a user's contract.
    """
    contract = db_get_contract(user.id, contract_id)
    
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract '{contract_id}' not found",
        )
    
    db_delete_contract(UUID(contract["id"]))
    return {"message": "Contract deleted"}


# =============================================================================
# Restriction Endpoints
# =============================================================================

@router.get("/restrictions", response_model=List[RestrictionSummary])
async def list_restrictions(
    source: Optional[str] = None,
    user: User = Depends(get_current_user),
):
    """
    List available restriction sets.
    
    Restriction sets define coding standards and certification rules.
    Returns both presets and user-created restriction sets.
    """
    restrictions = list(_mock_restrictions.values())
    
    # TODO: Add user's custom restrictions
    
    if source:
        restrictions = [r for r in restrictions if r["source"] == source]
    
    return [
        RestrictionSummary(
            id=r["id"],
            name=r["name"],
            version=r["version"],
            source=r["source"],
            authority=r.get("authority"),
            rule_count=len(r.get("rules", [])),
        )
        for r in restrictions
    ]


@router.get("/restrictions/presets", response_model=List[RestrictionSummary])
async def list_preset_restrictions():
    """
    List preset restriction sets (no authentication required).
    
    Presets include industry standards like:
    - NASA Power of 10
    - MISRA C (future)
    - DO-178C (future)
    """
    presets = [r for r in _mock_restrictions.values() if r["source"] == "preset"]
    
    return [
        RestrictionSummary(
            id=r["id"],
            name=r["name"],
            version=r["version"],
            source=r["source"],
            authority=r.get("authority"),
            rule_count=len(r.get("rules", [])),
        )
        for r in presets
    ]


@router.get("/restrictions/{restriction_id}", response_model=RestrictionDetail)
async def get_restriction(
    restriction_id: UUID,
    user: User = Depends(get_current_user),
):
    """
    Get full restriction set details.
    
    Returns complete restriction specification including all rules.
    """
    for restriction in _mock_restrictions.values():
        if restriction["id"] == restriction_id:
            return RestrictionDetail(**restriction)
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Restriction set '{restriction_id}' not found",
    )
