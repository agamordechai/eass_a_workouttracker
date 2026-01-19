"""Tests for authentication and authorization."""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

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

