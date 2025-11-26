# api/routes/auth.py
"""
Authentication endpoints.

Uses Supabase for authentication - verifies Supabase JWT tokens.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import jwt

from ..database import get_profile, get_profile_by_email


router = APIRouter(prefix="/auth")


# Load .env file if present
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

# Supabase JWT settings
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")


# Bearer token scheme
security = HTTPBearer(auto_error=False)


# =============================================================================
# Models
# =============================================================================

class User(BaseModel):
    """User model."""
    id: UUID
    email: str
    tier: str = "free"
    runs_this_month: int = 0
    runs_limit: int = 100
    is_active: bool = True


class UserResponse(BaseModel):
    """User response."""
    id: UUID
    email: str
    full_name: Optional[str] = None
    company: Optional[str] = None
    tier: str
    runs_this_month: int
    runs_limit: int
    created_at: datetime


# =============================================================================
# Dependencies
# =============================================================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Dependency to get current authenticated user from Supabase JWT token.
    
    Usage:
        @router.get("/protected")
        async def protected_route(user: User = Depends(get_current_user)):
            return {"user_id": user.id}
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    try:
        # Decode Supabase JWT
        # Note: In production, verify with Supabase JWT secret
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
            options={"verify_aud": False}  # Supabase tokens may have different audience
        )
        
        user_id = payload.get("sub")
        email = payload.get("email")
        
        if not user_id or not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
        
        # Get profile from database
        profile = get_profile(UUID(user_id))
        
        if not profile:
            # Profile should be auto-created by trigger, but handle edge case
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found",
            )
        
        return User(
            id=UUID(user_id),
            email=email,
            tier=profile.get("tier", "free"),
            runs_this_month=profile.get("runs_this_month", 0),
            runs_limit=profile.get("runs_limit", 100),
        )
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Optional[User]:
    """Dependency for optional authentication."""
    if not credentials:
        return None
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(user: User = Depends(get_current_user)):
    """
    Get current user information.
    
    Requires Supabase authentication token.
    """
    profile = get_profile(user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=UUID(profile["id"]),
        email=profile["email"],
        full_name=profile.get("full_name"),
        company=profile.get("company"),
        tier=profile.get("tier", "free"),
        runs_this_month=profile.get("runs_this_month", 0),
        runs_limit=profile.get("runs_limit", 100),
        created_at=profile["created_at"],
    )
