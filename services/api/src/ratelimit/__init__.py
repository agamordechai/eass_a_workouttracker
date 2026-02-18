"""Rate limiting module for Workout Tracker API."""

import logging

import jwt
from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from services.api.src.auth import ALGORITHM, SECRET_KEY, Role
from services.api.src.ratelimit.config import get_ratelimit_settings

logger = logging.getLogger(__name__)


def get_rate_limit_key(request: Request) -> str:
    """Get the rate limit key for a request.

    For authenticated requests: user:{username}:{role}
    For anonymous requests: ip:{client_ip}

    Args:
        request: The FastAPI request object.

    Returns:
        Rate limit key string.
    """
    # Try to extract JWT token from Authorization header
    auth_header = request.headers.get("Authorization", "")

    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            # Decode the JWT token to get username and role
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get("sub")
            role = payload.get("role", "user")

            if username:
                return f"user:{username}:{role}"
        except jwt.InvalidTokenError:
            # Token is invalid, fall back to IP-based limiting
            pass

    # Fall back to IP-based limiting for anonymous requests
    # Check X-Forwarded-For header (for requests behind proxy)
    client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    if not client_ip:
        # Fall back to direct client IP
        client_ip = request.client.host if request.client else "unknown"

    return f"ip:{client_ip}"


def get_rate_limit_for_request(request: Request, key: str) -> str:
    """Get the appropriate rate limit for a request based on role and endpoint.

    Args:
        request: The FastAPI request object.
        key: The rate limit key (from get_rate_limit_key).

    Returns:
        Rate limit string (e.g., "120/minute").
    """
    settings = get_ratelimit_settings()

    # Parse role from key
    if key.startswith("user:"):
        # Extract role from key: user:{username}:{role}
        parts = key.split(":")
        role_str = parts[2] if len(parts) >= 3 else "user"
        try:
            role = Role(role_str.lower())
        except ValueError:
            role = None  # anonymous
    else:
        # IP-based key means anonymous
        role = None

    # Check path patterns
    path = request.url.path

    # Auth endpoints have strict limits
    if path.startswith("/auth"):
        return settings.auth_limit

    # Admin endpoints
    if path.startswith("/admin"):
        return settings.admin_limit

    # Determine if this is a read or write operation
    is_read = request.method == "GET"

    # Return appropriate limit based on role and operation
    if is_read:
        if role == Role.ADMIN:
            return settings.read_limit_admin
        elif role == Role.USER or role == Role.READONLY:
            return settings.read_limit_user
        else:
            return settings.read_limit_anonymous
    else:
        # Write operation (POST, PATCH, DELETE, PUT)
        if role == Role.ADMIN:
            return settings.write_limit_admin
        elif role == Role.USER:
            return settings.write_limit_user
        else:
            return settings.write_limit_anonymous


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Custom handler for rate limit exceeded errors.

    Args:
        request: The FastAPI request object.
        exc: The RateLimitExceeded exception.

    Returns:
        JSONResponse with 429 status code.
    """
    # Extract retry_after from exception if available
    retry_after = getattr(exc, "retry_after", 60)

    # Log the rate limit violation
    key = get_rate_limit_key(request)
    logger.warning(f"Rate limit exceeded for {key} on {request.method} {request.url.path}")

    response = JSONResponse(
        status_code=429,
        content={
            "detail": f"Rate limit exceeded. Try again in {retry_after} seconds.",
            "retry_after": retry_after,
            "path": request.url.path,
        },
    )

    # Add Retry-After header
    response.headers["Retry-After"] = str(retry_after)

    return response


__all__ = [
    "get_rate_limit_key",
    "get_rate_limit_for_request",
    "rate_limit_exceeded_handler",
    "get_ratelimit_settings",
]
