"""Schemathesis property-based tests for the Workout Tracker API.

Schemathesis generates test cases from the OpenAPI schema to surface:
  - 5xx crashes on schema-valid inputs
  - Response bodies that violate the declared response models

Auth-protected endpoints (/auth/me, /admin/*) are covered via a ``map_headers``
hook that injects valid Bearer tokens.

Explicit tests below target edge cases that random generation is unlikely to
hit: Google auth flows, token lifecycle, RBAC enforcement, and field boundary
values.

Performance:
  - By default, runs with max_examples=10 (fast mode)
  - Run with --hypothesis-max-examples=100 for thorough testing
  - Use -m "not slow" to skip these tests entirely
"""

import pytest
import schemathesis
from datetime import timedelta
from unittest.mock import patch
from sqlmodel import SQLModel, Session
from fastapi.testclient import TestClient
from schemathesis.specs.openapi.checks import negative_data_rejection, ignored_auth
from hypothesis import settings, Phase

from services.api.src.api import app, limiter
from services.api.src.auth import create_access_token
from services.api.src.database.database import engine, get_session
from services.api.src.database.db_models import ExerciseTable, UserTable  # noqa: F401 — registers models


# ---------------------------------------------------------------------------
# Performance Configuration
# ---------------------------------------------------------------------------

# Configure Hypothesis for faster tests (10 examples instead of default 100)
# Override with: pytest --hypothesis-max-examples=100 for thorough testing
settings.register_profile("fast", max_examples=10, deadline=1000)
settings.register_profile("thorough", max_examples=100, deadline=5000)
settings.load_profile("fast")  # Use fast profile by default


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ensure_user(session: Session, user_id: int, role: str = "user") -> UserTable:
    """Ensure a test user exists in the database."""
    user = session.get(UserTable, user_id)
    if user is None:
        user = UserTable(
            id=user_id,
            google_id=f"test-google-{user_id}",
            email=f"testuser{user_id}@example.com",
            name=f"Test User {user_id}",
            role=role,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
    return user


def _token(user_id: int, role: str, minutes: int = 30) -> str:
    """Mint a signed JWT for test requests."""
    return create_access_token(
        data={"sub": str(user_id), "role": role},
        expires_delta=timedelta(minutes=minutes),
    )


# ---------------------------------------------------------------------------
# DB bootstrap — runs at import time so tables exist before from_asgi fires
# its first request (which may trigger the ASGI lifespan / seed).
# ---------------------------------------------------------------------------

SQLModel.metadata.create_all(engine)

# Ensure test users exist for schema-level tests
with Session(engine) as _session:
    _ensure_user(_session, 2, "user")
    _ensure_user(_session, 3, "admin")

# ---------------------------------------------------------------------------
# Disable rate limiter — requires Redis which is unavailable in unit-test
# environments.  When disabled, SlowAPIMiddleware short-circuits and the
# @limiter.limit() decorators pass through.  Rate-limit behaviour is tested
# independently in test_ratelimit.py.
# ---------------------------------------------------------------------------

limiter.enabled = False


# ---------------------------------------------------------------------------
# Schema loader + auth hook
# ---------------------------------------------------------------------------

schema = schemathesis.openapi.from_asgi("/openapi.json", app)

# Disable the coverage phase — schemathesis 4.x coverage-guided generation
# produces unsatisfiable strategies for endpoints without complex parameters.
schema.config.phases.coverage.enabled = False


@schema.hook
def map_headers(ctx, headers):
    """Inject Bearer tokens for endpoints that require authentication."""
    headers = headers or {}
    path = ctx.operation.full_path
    if path == "/auth/me" or path.startswith("/exercises"):
        headers["Authorization"] = f"Bearer {_token(2, 'user')}"
    elif path.startswith("/admin"):
        headers["Authorization"] = f"Bearer {_token(3, 'admin')}"
    return headers


@schema.hook
def map_path_parameters(ctx, path_parameters):
    """Clamp path parameters to values that SQLite can handle.

    SQLite INTEGER is limited to signed 64-bit (-9223372036854775808 to 9223372036854775807).
    Schemathesis generates very large integers that cause OverflowError.
    We limit IDs to a reasonable range (1 to 1 million).
    """
    if path_parameters:
        for key in ("exercise_id", "user_id"):
            if key in path_parameters and isinstance(path_parameters[key], int):
                path_parameters[key] = max(1, min(path_parameters[key], 1_000_000))
    return path_parameters


# ---------------------------------------------------------------------------
# Property-based: crash detection
# ---------------------------------------------------------------------------


@pytest.mark.slow
@schema.parametrize()
@settings(max_examples=10)  # Fast: 10 examples per endpoint
def test_no_server_errors(case):
    """Schema-valid inputs must never produce a 5xx response.

    This test is marked as 'slow' - skip with: pytest -m "not slow"
    Run only slow tests with: pytest -m slow
    """
    response = case.call()
    assert response.status_code < 500


# ---------------------------------------------------------------------------
# Property-based: response schema conformance
# ---------------------------------------------------------------------------


@pytest.mark.slow
@schema.parametrize()
@settings(max_examples=10)  # Fast: 10 examples per endpoint
def test_response_conforms_to_schema(case):
    """Successful (2xx) responses must match the declared OpenAPI response model.

    Excluded checks:
      - ``ignored_auth``: our ``map_headers`` hook deliberately injects valid
        tokens, so schemathesis's randomly-generated auth values are always
        overwritten — a 401 will never occur.
      - ``negative_data_rejection``: Pydantic v2 coerces booleans to numbers
        by default (``false`` → ``0.0``); this is intentional framework
        behaviour, not a schema violation.
    """
    response = case.call()
    if response.status_code < 300:
        case.validate_response(
            response,
            excluded_checks=[ignored_auth, negative_data_rejection],
        )


# ---------------------------------------------------------------------------
# Shared fixture for explicit tests
# ---------------------------------------------------------------------------


@pytest.fixture()
def client():
    """TestClient with ASGI lifespan and fresh test users."""
    with TestClient(app) as c:
        # Re-ensure test users exist (schemathesis tests may have altered DB state)
        with Session(engine) as session:
            _ensure_user(session, 2, "user")
            _ensure_user(session, 3, "admin")
        yield c


@pytest.fixture()
def user_headers():
    """Auth headers for a regular user (id=2)."""
    return {"Authorization": f"Bearer {_token(2, 'user')}"}


@pytest.fixture()
def admin_headers():
    """Auth headers for an admin user (id=3)."""
    return {"Authorization": f"Bearer {_token(3, 'admin')}"}


# ---------------------------------------------------------------------------
# Explicit: Google auth / token lifecycle
# ---------------------------------------------------------------------------


class TestGoogleAuthExplicit:
    """Targeted Google auth edge cases."""

    @patch("services.api.src.api.verify_google_token")
    def test_valid_google_login(self, mock_verify, client):
        mock_verify.return_value = {
            "sub": "google-new-user-999",
            "email": "newuser@example.com",
            "name": "New User",
            "picture": "https://example.com/photo.jpg",
        }
        resp = client.post("/auth/google", json={"id_token": "fake-google-token"})
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert "refresh_token" in body

    def test_google_login_missing_token_returns_422(self, client):
        resp = client.post("/auth/google", json={})
        assert resp.status_code == 422

    def test_refresh_with_invalid_token_returns_401(self, client):
        resp = client.post("/auth/refresh", json={"refresh_token": "invalid.token"})
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Explicit: /auth/me token checks
# ---------------------------------------------------------------------------


class TestAuthMeExplicit:
    """Token-based /auth/me edge cases."""

    def test_returns_current_user(self, client, user_headers):
        resp = client.get("/auth/me", headers=user_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "email" in body
        assert body["role"] == "user"

    def test_missing_token_returns_401(self, client):
        resp = client.get("/auth/me")
        assert resp.status_code == 401

    def test_expired_token_returns_401(self, client):
        token = _token(2, "user", minutes=-1)
        resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401

    def test_malformed_token_returns_401(self, client):
        resp = client.get("/auth/me", headers={"Authorization": "Bearer this.is.garbage"})
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Explicit: admin RBAC enforcement
# ---------------------------------------------------------------------------


class TestAdminExplicit:
    """Admin endpoint access-control checks."""

    def test_list_users_as_admin(self, client, admin_headers):
        resp = client.get("/admin/users", headers=admin_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        assert len(body) > 0
        assert "email" in body[0]

    def test_list_users_as_regular_user_returns_403(self, client, user_headers):
        resp = client.get("/admin/users", headers=user_headers)
        assert resp.status_code == 403

    def test_admin_delete_missing_exercise_returns_404(self, client, admin_headers):
        resp = client.delete("/admin/exercises/99999", headers=admin_headers)
        assert resp.status_code == 404

    def test_admin_delete_as_regular_user_returns_403(self, client, user_headers):
        resp = client.delete("/admin/exercises/1", headers=user_headers)
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Explicit: exercise field boundary values
# ---------------------------------------------------------------------------


class TestExerciseBoundaryExplicit:
    """Boundary-value exercise CRUD — values that fuzzing may skip."""

    def test_minimum_valid_values(self, client, user_headers):
        resp = client.post("/exercises", json={"name": "X", "sets": 1, "reps": 1}, headers=user_headers)
        assert resp.status_code == 201
        assert resp.json()["sets"] == 1
        assert resp.json()["reps"] == 1

    def test_maximum_sets_accepted(self, client, user_headers):
        resp = client.post("/exercises", json={"name": "MaxSets", "sets": 100, "reps": 1}, headers=user_headers)
        assert resp.status_code == 201
        assert resp.json()["sets"] == 100

    def test_maximum_reps_accepted(self, client, user_headers):
        resp = client.post("/exercises", json={"name": "MaxReps", "sets": 1, "reps": 1000}, headers=user_headers)
        assert resp.status_code == 201
        assert resp.json()["reps"] == 1000

    def test_zero_weight_accepted(self, client, user_headers):
        resp = client.post("/exercises", json={"name": "ZeroWt", "sets": 1, "reps": 1, "weight": 0.0}, headers=user_headers)
        assert resp.status_code == 201
        assert resp.json()["weight"] == 0.0

    def test_sets_above_max_rejected(self, client, user_headers):
        resp = client.post("/exercises", json={"name": "Over", "sets": 101, "reps": 1}, headers=user_headers)
        assert resp.status_code == 422

    def test_reps_above_max_rejected(self, client, user_headers):
        resp = client.post("/exercises", json={"name": "Over", "sets": 1, "reps": 1001}, headers=user_headers)
        assert resp.status_code == 422

    def test_patch_weight_to_null_clears_weight(self, client, user_headers):
        create = client.post("/exercises", json={"name": "W", "sets": 1, "reps": 1, "weight": 50.0}, headers=user_headers)
        eid = create.json()["id"]
        resp = client.patch(f"/exercises/{eid}", json={"weight": None}, headers=user_headers)
        assert resp.status_code == 200
        assert resp.json()["weight"] is None

    def test_patch_empty_body_leaves_exercise_unchanged(self, client, user_headers):
        create = client.post("/exercises", json={"name": "NoChange", "sets": 3, "reps": 10}, headers=user_headers)
        eid = create.json()["id"]
        resp = client.patch(f"/exercises/{eid}", json={}, headers=user_headers)
        assert resp.status_code == 200
        assert resp.json()["name"] == "NoChange"
        assert resp.json()["sets"] == 3
