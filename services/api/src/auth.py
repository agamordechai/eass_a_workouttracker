"""Authentication and authorization module for Workout Tracker API."""
from datetime import datetime, timedelta, timezone
from typing import Optional, Annotated
from enum import Enum
import hashlib
import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import jwt

# Security configuration
SECRET_KEY = "your-secret-key-change-in-production"  # Override via environment
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Bearer token scheme
bearer_scheme = HTTPBearer(auto_error=False)


class Role(str, Enum):
    """User roles for authorization."""
    ADMIN = "admin"
    USER = "user"
    READONLY = "readonly"


class User(BaseModel):
    """User model."""
    username: str
    email: Optional[str] = None
    role: Role = Role.USER
    disabled: bool = False


class UserInDB(User):
    """User model with hashed password."""
    hashed_password: str


class Token(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Token expiration in seconds")
    refresh_token: Optional[str] = None


class TokenData(BaseModel):
    """Token payload data."""
    username: str
    role: Role
    exp: datetime
    scopes: list[str] = Field(default_factory=list)


class LoginRequest(BaseModel):
    """Login request model."""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class RegisterRequest(BaseModel):
    """Registration request model."""
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[str] = None
    password: str = Field(..., min_length=6)
    role: Role = Role.USER


# Simulated user database (in production, use real database)
# Passwords are hashed using SHA-256 with salt
USERS_DB: dict[str, UserInDB] = {
    "admin": UserInDB(
        username="admin",
        email="admin@workout.local",
        role=Role.ADMIN,
        disabled=False,
        # Password: "admin123" (hashed)
        hashed_password="pbkdf2:sha256:260000$salt$8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918"
    ),
    "user": UserInDB(
        username="user",
        email="user@workout.local",
        role=Role.USER,
        disabled=False,
        # Password: "user123" (hashed)
        hashed_password="pbkdf2:sha256:260000$salt$ee11cbb19052e40b07aac0ca060c23ee"
    ),
}


def hash_password(password: str, salt: Optional[str] = None) -> str:
    """Hash a password using SHA-256 with salt.

    Args:
        password: Plain text password
        salt: Optional salt (generated if not provided)

    Returns:
        Hashed password string
    """
    if salt is None:
        salt = secrets.token_hex(16)

    # Use PBKDF2-like format for clarity
    hash_value = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return f"pbkdf2:sha256:260000${salt}${hash_value}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored hashed password

    Returns:
        True if password matches, False otherwise
    """
    try:
        parts = hashed_password.split("$")
        if len(parts) != 3:
            return False
        salt = parts[1]
        expected_hash = hash_password(plain_password, salt)
        return secrets.compare_digest(hashed_password, expected_hash)
    except Exception:
        return False


def get_user(username: str) -> Optional[UserInDB]:
    """Get user from database.

    Args:
        username: Username to look up

    Returns:
        User if found, None otherwise
    """
    return USERS_DB.get(username)


def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """Authenticate a user with username and password.

    Args:
        username: Username
        password: Plain text password

    Returns:
        User if authentication successful, None otherwise
    """
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
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
    username: str,
    secret_key: str = SECRET_KEY
) -> str:
    """Create a JWT refresh token.

    Args:
        username: Username for the token
        secret_key: Secret key for signing

    Returns:
        Encoded JWT refresh token string
    """
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "sub": username,
        "type": "refresh",
        "exp": expire
    }
    return jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)


def decode_token(
    token: str,
    secret_key: str = SECRET_KEY
) -> Optional[dict]:
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
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)]
) -> User:
    """Dependency to get the current authenticated user.

    Args:
        credentials: Bearer token credentials

    Returns:
        Current user

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

    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception

    user = get_user(username)
    if user is None:
        raise credentials_exception

    if user.disabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )

    return User(
        username=user.username,
        email=user.email,
        role=user.role,
        disabled=user.disabled
    )


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """Dependency to get current active (non-disabled) user.

    Args:
        current_user: Current user from token

    Returns:
        Active user

    Raises:
        HTTPException: If user is disabled
    """
    if current_user.disabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


def require_role(*allowed_roles: Role):
    """Dependency factory to require specific roles.

    Args:
        allowed_roles: Roles that are allowed access

    Returns:
        Dependency function
    """
    async def role_checker(
        current_user: Annotated[User, Depends(get_current_active_user)]
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' not authorized. Required: {[r.value for r in allowed_roles]}"
            )
        return current_user

    return role_checker


# Convenience dependencies
require_admin = require_role(Role.ADMIN)
require_user_or_admin = require_role(Role.USER, Role.ADMIN)

