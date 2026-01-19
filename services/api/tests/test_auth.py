"""Tests for authentication and authorization."""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from fastapi.testclient import TestClient

from services.api.src.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    authenticate_user,
    get_user,
    Role,
    User,
    UserInDB,
    SECRET_KEY,
    ALGORITHM
)
from services.api.src.api import app


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_hash_password_creates_hash(self):
        """Test that hash_password creates a valid hash."""
        password = "mysecretpassword"
        hashed = hash_password(password)

        assert hashed.startswith("pbkdf2:sha256:")
        assert "$" in hashed
        assert password not in hashed

    def test_hash_password_different_each_time(self):
        """Test that hashing same password twice gives different hashes (salt)."""
        password = "mysecretpassword"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Different salts should produce different hashes
        assert hash1 != hash2

    def test_hash_password_with_explicit_salt(self):
        """Test hashing with explicit salt is deterministic."""
        password = "mysecretpassword"
        salt = "testsalt123"

        hash1 = hash_password(password, salt)
        hash2 = hash_password(password, salt)

        assert hash1 == hash2

    def test_verify_password_correct(self):
        """Test verifying correct password."""
        password = "mysecretpassword"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test verifying incorrect password."""
        password = "mysecretpassword"
        hashed = hash_password(password)

        assert verify_password("wrongpassword", hashed) is False

    def test_verify_password_invalid_hash_format(self):
        """Test verifying against invalid hash format."""
        assert verify_password("password", "invalid_hash") is False
        assert verify_password("password", "") is False


class TestJWTTokens:
    """Tests for JWT token creation and validation."""

    def test_create_access_token(self):
        """Test creating an access token."""
        data = {"sub": "testuser", "role": "user"}
        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_expiry(self):
        """Test creating token with custom expiry."""
        data = {"sub": "testuser"}
        expires = timedelta(hours=1)
        token = create_access_token(data, expires_delta=expires)

        decoded = decode_token(token)
        assert decoded is not None
        assert decoded["sub"] == "testuser"

    def test_decode_valid_token(self):
        """Test decoding a valid token."""
        data = {"sub": "testuser", "role": "admin"}
        token = create_access_token(data)

        decoded = decode_token(token)

        assert decoded is not None
        assert decoded["sub"] == "testuser"
        assert decoded["role"] == "admin"
        assert "exp" in decoded

    def test_decode_expired_token(self):
        """Test that expired tokens return None."""
        data = {"sub": "testuser"}
        # Create token that expires immediately
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
        data = {"sub": "testuser"}
        token = create_access_token(data, secret_key="different-secret")

        # Try to decode with default secret
        decoded = decode_token(token)
        assert decoded is None

    def test_create_refresh_token(self):
        """Test creating a refresh token."""
        token = create_refresh_token("testuser")

        assert token is not None
        decoded = decode_token(token)
        assert decoded["sub"] == "testuser"
        assert decoded["type"] == "refresh"


class TestUserAuthentication:
    """Tests for user authentication."""

    def test_get_existing_user(self):
        """Test getting an existing user."""
        user = get_user("admin")

        assert user is not None
        assert user.username == "admin"
        assert user.role == Role.ADMIN

    def test_get_nonexistent_user(self):
        """Test getting a user that doesn't exist."""
        user = get_user("nonexistent")
        assert user is None

    def test_authenticate_user_invalid_username(self):
        """Test authentication with invalid username."""
        result = authenticate_user("nonexistent", "password")
        assert result is None

    def test_authenticate_user_invalid_password(self):
        """Test authentication with invalid password."""
        result = authenticate_user("admin", "wrongpassword")
        assert result is None


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


class TestUserModels:
    """Tests for user Pydantic models."""

    def test_user_model(self):
        """Test User model creation."""
        user = User(username="test", role=Role.USER)

        assert user.username == "test"
        assert user.role == Role.USER
        assert user.disabled is False
        assert user.email is None

    def test_user_in_db_model(self):
        """Test UserInDB model with hashed password."""
        user = UserInDB(
            username="test",
            role=Role.USER,
            hashed_password="somehash"
        )

        assert user.hashed_password == "somehash"


# Fixture for TestClient
@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def user_token():
    """Create a valid token for a regular user."""
    return create_access_token(
        data={"sub": "user", "role": "user"},
        expires_delta=timedelta(minutes=30)
    )


@pytest.fixture
def admin_token():
    """Create a valid token for an admin user."""
    return create_access_token(
        data={"sub": "admin", "role": "admin"},
        expires_delta=timedelta(minutes=30)
    )


@pytest.fixture
def expired_token():
    """Create an expired token."""
    return create_access_token(
        data={"sub": "user", "role": "user"},
        expires_delta=timedelta(seconds=-1)
    )


class TestProtectedEndpoints:
    """Integration tests for protected API endpoints.

    These tests verify that role-based access control works correctly
    by testing the actual API endpoints with different tokens.
    """

    def test_auth_me_without_token_returns_401(self, client):
        """Test that /auth/me returns 401 when no token is provided."""
        response = client.get("/auth/me")

        assert response.status_code == 401
        assert "Could not validate credentials" in response.json()["detail"]

    def test_auth_me_with_expired_token_returns_401(self, client, expired_token):
        """Test that /auth/me returns 401 when token is expired."""
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )

        assert response.status_code == 401
        assert "Could not validate credentials" in response.json()["detail"]

    def test_auth_me_with_invalid_token_returns_401(self, client):
        """Test that /auth/me returns 401 when token is invalid."""
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"}
        )

        assert response.status_code == 401
        assert "Could not validate credentials" in response.json()["detail"]

    def test_auth_me_with_valid_user_token_succeeds(self, client, user_token):
        """Test that /auth/me succeeds with valid user token."""
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "user"
        assert data["role"] == "user"

    def test_admin_users_without_token_returns_401(self, client):
        """Test that /admin/users returns 401 when no token is provided."""
        response = client.get("/admin/users")

        assert response.status_code == 401
        assert "Could not validate credentials" in response.json()["detail"]

    def test_admin_users_with_user_role_returns_403(self, client, user_token):
        """Test that /admin/users returns 403 when user lacks admin scope.

        This is the key test for 'missing scope' - a valid token but
        insufficient permissions should return 403 Forbidden.
        """
        response = client.get(
            "/admin/users",
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 403
        assert "not authorized" in response.json()["detail"].lower()
        assert "admin" in response.json()["detail"].lower()

    def test_admin_users_with_admin_role_succeeds(self, client, admin_token):
        """Test that /admin/users succeeds with admin token."""
        response = client.get(
            "/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should contain at least admin and user
        usernames = [u["username"] for u in data]
        assert "admin" in usernames
        assert "user" in usernames

    def test_admin_delete_exercise_with_user_role_returns_403(self, client, user_token):
        """Test that /admin/exercises/{id} DELETE returns 403 for non-admin.

        Tests that admin-protected endpoints reject users without admin scope.
        """
        response = client.delete(
            "/admin/exercises/999",
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 403
        assert "not authorized" in response.json()["detail"].lower()

    def test_admin_delete_exercise_with_expired_token_returns_401(self, client, expired_token):
        """Test that /admin/exercises/{id} DELETE returns 401 for expired token."""
        response = client.delete(
            "/admin/exercises/999",
            headers={"Authorization": f"Bearer {expired_token}"}
        )

        assert response.status_code == 401


class TestLoginEndpoint:
    """Tests for the /auth/login endpoint."""

    def test_login_with_valid_credentials(self, client):
        """Test successful login returns tokens."""
        response = client.post(
            "/auth/login",
            json={"username": "admin", "password": "admin123"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

    def test_login_with_invalid_username(self, client):
        """Test login with invalid username returns 401."""
        response = client.post(
            "/auth/login",
            json={"username": "nonexistent", "password": "password123"}
        )

        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

    def test_login_with_invalid_password(self, client):
        """Test login with invalid password returns 401."""
        response = client.post(
            "/auth/login",
            json={"username": "admin", "password": "wrongpassword"}
        )

        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

    def test_login_token_can_access_protected_route(self, client):
        """Test that token from login can access protected routes."""
        # Login first
        login_response = client.post(
            "/auth/login",
            json={"username": "user", "password": "user123"}
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Use token to access protected route
        me_response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert me_response.status_code == 200
        assert me_response.json()["username"] == "user"

