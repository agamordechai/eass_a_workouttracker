"""Authentication and authorization module for Workout Tracker API.

Uses Google OAuth 2.0 ID tokens for sign-in. JWTs are issued locally
after verifying the Google token.
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Annotated
from enum import Enum

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlmodel import Session
import jwt
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests
import bcrypt

from services.api.src.database.database import get_session
from services.api.src.database.db_models import UserTable

# Security configuration
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Bearer token scheme
bearer_scheme = HTTPBearer(auto_error=False)

def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt.

    Args:
        password: Plaintext password

    Returns:
        Bcrypt hash string
    """
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash.

    Args:
        plain_password: Plaintext password to check
        hashed_password: Stored bcrypt hash

    Returns:
        True if the password matches
    """
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


class Role(str, Enum):
    """User roles for authorization."""
    ADMIN = "admin"
    USER = "user"
    READONLY = "readonly"


class Token(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Token expiration in seconds")
    refresh_token: str | None = None


class GoogleLoginRequest(BaseModel):
    """Google sign-in request model."""
    id_token: str = Field(..., description="Google OAuth ID token from frontend")


class RefreshRequest(BaseModel):
    """Token refresh request model."""
    refresh_token: str = Field(..., description="Refresh token")


class RegisterRequest(BaseModel):
    """Email/password registration request model."""
    email: EmailStr = Field(..., description="User email address")
    name: str = Field(..., min_length=1, max_length=255, description="Display name")
    password: str = Field(..., min_length=8, max_length=128, description="Password (min 8 characters)")

    @field_validator('email')
    @classmethod
    def validate_email_domain(cls, v: str) -> str:
        """Validate email domain and check for common typos."""
        domain = v.split('@')[1].lower()

        # Common domain typos
        typos = {
            'gmial.com': 'gmail.com', 'gmaik.com': 'gmail.com', 'gmal.com': 'gmail.com',
            'gmail.co': 'gmail.com', 'gmail.cm': 'gmail.com', 'gmail.con': 'gmail.com',
            'gmai.com': 'gmail.com', 'gamil.com': 'gmail.com', 'gnail.com': 'gmail.com',
            'yaho.com': 'yahoo.com', 'yahoo.co': 'yahoo.com', 'yahoo.con': 'yahoo.com',
            'hotmal.com': 'hotmail.com', 'hotmail.co': 'hotmail.com', 'hotmail.con': 'hotmail.com',
            'outlok.com': 'outlook.com', 'outlook.co': 'outlook.com', 'outlook.con': 'outlook.com',
            'icloud.co': 'icloud.com', 'icloud.con': 'icloud.com',
        }

        if domain in typos:
            suggestion = v.replace(domain, typos[domain])
            raise ValueError(f"Invalid email domain. Did you mean {suggestion}?")

        # Check for suspicious TLDs
        if domain.endswith(('.con', '.cm', '.vom', '.cpm')):
            raise ValueError("Invalid email domain. Please check your email address.")

        return v


class EmailLoginRequest(BaseModel):
    """Email/password login request model."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class UpdateProfileRequest(BaseModel):
    """Profile update request model."""
    name: str | None = Field(None, min_length=1, max_length=255, description="Display name")


class UserResponse(BaseModel):
    """Public user information returned by API."""
    id: int
    email: str
    name: str
    picture_url: str | None = None
    role: str


class AdminUserResponse(BaseModel):
    """User info returned by admin endpoints."""
    id: int
    email: str
    name: str
    picture_url: str | None = None
    role: str
    disabled: bool
    created_at: datetime
    exercise_count: int


class AdminUpdateUserRequest(BaseModel):
    """Request to update a user's role or disabled status (admin only)."""
    role: str | None = Field(None, pattern=r"^(admin|user|readonly)$")
    disabled: bool | None = None


class AdminStatsResponse(BaseModel):
    """Platform-wide statistics for admin dashboard."""
    total_users: int
    total_exercises: int
    recent_signups_7d: int
    active_users_7d: int


def verify_google_token(token: str, client_id: str) -> dict:
    """Verify a Google OAuth ID token and return user info.

    Args:
        token: Google ID token string from the frontend
        client_id: Google OAuth Client ID for audience verification

    Returns:
        Parsed Google user info dict with keys: sub, email, name, picture

    Raises:
        HTTPException: If the token is invalid or verification fails
    """
    try:
        idinfo = google_id_token.verify_oauth2_token(
            token, google_requests.Request(), client_id
        )
        return {
            "sub": idinfo["sub"],
            "email": idinfo.get("email", ""),
            "name": idinfo.get("name", ""),
            "picture": idinfo.get("picture"),
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google token: {e}",
        )


def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None,
    secret_key: str = SECRET_KEY
) -> str:
    """Create a JWT access token.

    Args:
        data: Payload data to encode
        expires_delta: Optional custom expiration time
        secret_key: Secret key for signing

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)


def create_refresh_token(
    user_id: int,
    secret_key: str = SECRET_KEY
) -> str:
    """Create a JWT refresh token.

    Args:
        user_id: User ID for the token subject
        secret_key: Secret key for signing

    Returns:
        Encoded JWT refresh token string
    """
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expire
    }
    return jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)


def decode_token(
    token: str,
    secret_key: str = SECRET_KEY
) -> dict | None:
    """Decode and verify a JWT token.

    Args:
        token: JWT token string
        secret_key: Secret key for verification

    Returns:
        Decoded payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: Annotated[Session, Depends(get_session)],
) -> UserTable:
    """Dependency to get the current authenticated user from the database.

    Args:
        credentials: Bearer token credentials
        session: Database session

    Returns:
        Current user's UserTable row

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise credentials_exception

    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        raise credentials_exception

    user_id_str: str | None = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise credentials_exception

    user = session.get(UserTable, user_id)
    if user is None:
        raise credentials_exception

    if user.disabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )

    return user


def require_role(*allowed_roles: Role):
    """Dependency factory to require specific roles.

    Args:
        allowed_roles: Roles that are allowed access

    Returns:
        Dependency function
    """
    async def role_checker(
        current_user: Annotated[UserTable, Depends(get_current_user)]
    ) -> UserTable:
        if current_user.role not in [r.value for r in allowed_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' not authorized. Required: {[r.value for r in allowed_roles]}"
            )
        return current_user

    return role_checker


# Convenience dependencies
require_admin = require_role(Role.ADMIN)
require_user_or_admin = require_role(Role.USER, Role.ADMIN)
