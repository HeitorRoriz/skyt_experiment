# api/routes/contracts.py
"""
Contract and restriction endpoints.

Browse available contracts and manage restriction sets.
"""

from typing import Optional, List
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from .auth import get_current_user, User


router = APIRouter()


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
# Mock Data (Replace with repository pattern)
# =============================================================================

_mock_contracts = {
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
    "binary_search": {
        "id": "binary_search",
        "version": "1.0.0",
        "task_intent": "Search for target in sorted array using binary search",
        "prompt": "Write a Python function called 'binary_search' that takes a sorted list of integers and a target value...",
        "description": "Binary search with boundary conditions",
        "algorithm_family": "searching",
        "constraints": {"function_name": "binary_search", "implementation_style": "iterative"},
        "oracle_requirements": {"test_cases": [{"input": [[1,2,3], 2], "expected": 1}]},
        "rescue_bounds": {"max_transformations": 5},
    },
    "slugify": {
        "id": "slugify",
        "version": "1.0.0",
        "task_intent": "Convert string to URL-friendly slug format",
        "prompt": "Write a Python function called 'slugify' that takes a string and converts it to a URL-friendly slug...",
        "description": "String slugification for URLs",
        "algorithm_family": "string_transformation",
        "constraints": {"function_name": "slugify"},
        "oracle_requirements": {"test_cases": [{"input": "Hello World", "expected": "hello-world"}]},
        "rescue_bounds": {"max_transformations": 5},
    },
    "balanced_brackets": {
        "id": "balanced_brackets",
        "version": "1.0.0",
        "task_intent": "Check if brackets in string are balanced",
        "prompt": "Write a Python function called 'is_balanced' that takes a string containing brackets...",
        "description": "Bracket balancing validation using stack",
        "algorithm_family": "stack",
        "constraints": {"function_name": "is_balanced"},
        "oracle_requirements": {"test_cases": [{"input": "()", "expected": True}]},
        "rescue_bounds": {"max_transformations": 5},
    },
}

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

@router.get("/contracts", response_model=List[ContractSummary])
async def list_contracts(
    algorithm_family: Optional[str] = None,
):
    """
    List available contracts.
    
    Contracts define code generation requirements including:
    - Task intent (what the code should do)
    - Constraints (function names, style)
    - Oracle requirements (test cases)
    
    No authentication required - contracts are public.
    """
    contracts = list(_mock_contracts.values())
    
    if algorithm_family:
        contracts = [c for c in contracts if c["algorithm_family"] == algorithm_family]
    
    return [
        ContractSummary(
            id=c["id"],
            version=c["version"],
            task_intent=c["task_intent"],
            algorithm_family=c["algorithm_family"],
            test_count=len(c["oracle_requirements"].get("test_cases", [])),
        )
        for c in contracts
    ]


@router.get("/contracts/{contract_id}", response_model=ContractDetail)
async def get_contract(contract_id: str):
    """
    Get full contract details.
    
    Returns complete contract specification including prompt and test cases.
    """
    contract = _mock_contracts.get(contract_id)
    
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract '{contract_id}' not found",
        )
    
    return ContractDetail(**contract)


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
