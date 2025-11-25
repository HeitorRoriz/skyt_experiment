# api/routes/auth.py
"""
Authentication endpoints.

Provides JWT-based authentication for the SKYT API.
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
import jwt

from ..config import settings


router = APIRouter(prefix="/auth")


# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_prefix}/auth/token")


# =============================================================================
# Models
# =============================================================================

class User(BaseModel):
    """User model."""
    id: UUID
    email: str
    subscription_tier: str = "free"  # free, pro, enterprise
    is_active: bool = True


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Token payload data."""
    user_id: UUID
    email: str
    subscription_tier: str


class UserCreate(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User response (no password)."""
    id: UUID
    email: str
    subscription_tier: str
    created_at: datetime


# =============================================================================
# Mock User Store (Replace with database in production)
# =============================================================================

# In-memory user store for development
_mock_users = {
    "demo@skyt.works": {
        "id": uuid4(),
        "email": "demo@skyt.works",
        "password_hash": "demo123",  # In production: use bcrypt
        "subscription_tier": "pro",
        "is_active": True,
        "created_at": datetime.utcnow(),
    }
}


def get_user_by_email(email: str) -> Optional[dict]:
    """Get user from store."""
    return _mock_users.get(email)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password. TODO: Use bcrypt in production."""
    return plain_password == hashed_password


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=settings.jwt_expiration_hours))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


# =============================================================================
# Dependencies
# =============================================================================

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Dependency to get current authenticated user from JWT token.
    
    Usage:
        @router.get("/protected")
        async def protected_route(user: User = Depends(get_current_user)):
            return {"user_id": user.id}
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("user_id")
        email = payload.get("email")
        subscription_tier = payload.get("subscription_tier", "free")
        
        if user_id is None or email is None:
            raise credentials_exception
            
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise credentials_exception
    
    return User(
        id=UUID(user_id),
        email=email,
        subscription_tier=subscription_tier,
    )


async def get_optional_user(token: str = Depends(oauth2_scheme)) -> Optional[User]:
    """Dependency for optional authentication."""
    try:
        return await get_current_user(token)
    except HTTPException:
        return None


# =============================================================================
# Endpoints
# =============================================================================

@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token login.
    
    Get an access token for API authentication.
    
    - **username**: Email address
    - **password**: Password
    """
    user = get_user_by_email(form_data.username)
    
    if not user or not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={
            "user_id": str(user["id"]),
            "email": user["email"],
            "subscription_tier": user["subscription_tier"],
        }
    )
    
    return Token(
        access_token=access_token,
        expires_in=settings.jwt_expiration_hours * 3600,
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """
    Register a new user.
    
    Creates a new account with free tier subscription.
    """
    if get_user_by_email(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    new_user = {
        "id": uuid4(),
        "email": user_data.email,
        "password_hash": user_data.password,  # TODO: Hash with bcrypt
        "subscription_tier": "free",
        "is_active": True,
        "created_at": datetime.utcnow(),
    }
    
    _mock_users[user_data.email] = new_user
    
    return UserResponse(
        id=new_user["id"],
        email=new_user["email"],
        subscription_tier=new_user["subscription_tier"],
        created_at=new_user["created_at"],
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(user: User = Depends(get_current_user)):
    """
    Get current user information.
    
    Requires authentication.
    """
    user_data = get_user_by_email(user.email)
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=user_data["id"],
        email=user_data["email"],
        subscription_tier=user_data["subscription_tier"],
        created_at=user_data["created_at"],
    )
