"""Tests for authentication and authorization (Google OAuth)."""

from datetime import timedelta
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from services.api.src.api import app, limiter
from services.api.src.auth import (
    Role,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_google_token,
)
from services.api.src.database.db_models import UserTable

# Disable rate limiter for tests (requires Redis which may not be available)
limiter.enabled = False


class TestJWTTokens:
    """Tests for JWT token creation and validation."""

    def test_create_access_token(self):
        """Test creating an access token."""
        data = {"sub": "1", "role": "user"}
        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_expiry(self):
        """Test creating token with custom expiry."""
        data = {"sub": "1"}
        expires = timedelta(hours=1)
        token = create_access_token(data, expires_delta=expires)

        decoded = decode_token(token)
        assert decoded is not None
        assert decoded["sub"] == "1"

    def test_decode_valid_token(self):
        """Test decoding a valid token."""
        data = {"sub": "1", "role": "admin"}
        token = create_access_token(data)

        decoded = decode_token(token)

        assert decoded is not None
        assert decoded["sub"] == "1"
        assert decoded["role"] == "admin"
        assert "exp" in decoded

    def test_decode_expired_token(self):
        """Test that expired tokens return None."""
        data = {"sub": "1"}
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))

        decoded = decode_token(token)
        assert decoded is None

    def test_decode_invalid_token(self):
        """Test that invalid tokens return None."""
        assert decode_token("invalid.token.here") is None
        assert decode_token("") is None
        assert decode_token("notavalidjwt") is None

    def test_decode_token_wrong_secret(self):
        """Test that token signed with different secret fails."""
        data = {"sub": "1"}
        token = create_access_token(data, secret_key="different-secret")

        decoded = decode_token(token)
        assert decoded is None

    def test_create_refresh_token(self):
        """Test creating a refresh token."""
        token = create_refresh_token(42)

        assert token is not None
        decoded = decode_token(token)
        assert decoded["sub"] == "42"
        assert decoded["type"] == "refresh"


class TestGoogleTokenVerification:
    """Tests for Google ID token verification."""

    @patch("services.api.src.auth.google_id_token.verify_oauth2_token")
    def test_verify_google_token_success(self, mock_verify):
        """Test successful Google token verification."""
        mock_verify.return_value = {
            "sub": "google-123",
            "email": "user@example.com",
            "name": "Test User",
            "picture": "https://example.com/photo.jpg",
        }

        result = verify_google_token("fake-token", "fake-client-id")

        assert result["sub"] == "google-123"
        assert result["email"] == "user@example.com"
        assert result["name"] == "Test User"
        assert result["picture"] == "https://example.com/photo.jpg"

    @patch("services.api.src.auth.google_id_token.verify_oauth2_token")
    def test_verify_google_token_invalid(self, mock_verify):
        """Test that invalid Google token raises HTTPException."""
        mock_verify.side_effect = ValueError("Token is invalid")

        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            verify_google_token("bad-token", "fake-client-id")
        assert exc_info.value.status_code == 401


class TestRoles:
    """Tests for role enumeration."""

    def test_role_values(self):
        """Test role enum values."""
        assert Role.ADMIN.value == "admin"
        assert Role.USER.value == "user"
        assert Role.READONLY.value == "readonly"

    def test_role_from_string(self):
        """Test creating role from string."""
        assert Role("admin") == Role.ADMIN
        assert Role("user") == Role.USER


# Fixture for TestClient
@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


def _create_test_user(session: Session, user_id: int = 2) -> UserTable:
    """Helper to create a test user in the database."""
    user = UserTable(
        id=user_id,
        google_id=f"test-google-{user_id}",
        email=f"testuser{user_id}@example.com",
        name=f"Test User {user_id}",
        role="user",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def _create_admin_user(session: Session, user_id: int = 3) -> UserTable:
    """Helper to create an admin user in the database."""
    user = UserTable(
        id=user_id,
        google_id=f"admin-google-{user_id}",
        email=f"admin{user_id}@example.com",
        name=f"Admin User {user_id}",
        role="admin",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def user_token():
    """Create a valid token for a regular user (id=2)."""
    return create_access_token(data={"sub": "2", "role": "user"}, expires_delta=timedelta(minutes=30))


@pytest.fixture
def admin_token():
    """Create a valid token for an admin user (id=3)."""
    return create_access_token(data={"sub": "3", "role": "admin"}, expires_delta=timedelta(minutes=30))


@pytest.fixture
def expired_token():
    """Create an expired token."""
    return create_access_token(data={"sub": "2", "role": "user"}, expires_delta=timedelta(seconds=-1))


class TestProtectedEndpoints:
    """Integration tests for protected API endpoints."""

    def test_auth_me_without_token_returns_401(self, client):
        """Test that /auth/me returns 401 when no token is provided."""
        response = client.get("/auth/me")

        assert response.status_code == 401
        assert "Could not validate credentials" in response.json()["detail"]

    def test_auth_me_with_expired_token_returns_401(self, client, expired_token):
        """Test that /auth/me returns 401 when token is expired."""
        response = client.get("/auth/me", headers={"Authorization": f"Bearer {expired_token}"})

        assert response.status_code == 401
        assert "Could not validate credentials" in response.json()["detail"]

    def test_auth_me_with_invalid_token_returns_401(self, client):
        """Test that /auth/me returns 401 when token is invalid."""
        response = client.get("/auth/me", headers={"Authorization": "Bearer invalid.token.here"})

        assert response.status_code == 401
        assert "Could not validate credentials" in response.json()["detail"]
