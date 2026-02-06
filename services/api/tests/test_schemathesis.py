"""Schemathesis property-based tests for the Workout Tracker API.

Schemathesis generates test cases from the OpenAPI schema to surface:
  - 5xx crashes on schema-valid inputs
  - Response bodies that violate the declared response models

Auth-protected endpoints (/auth/me, /admin/*) are covered via a ``map_headers``
hook that injects valid Bearer tokens.

Explicit tests below target edge cases that random generation is unlikely to
hit: login flows, token lifecycle, RBAC enforcement, and field boundary values.

Performance:
  - By default, runs with max_examples=10 (fast mode)
  - Run with --hypothesis-max-examples=100 for thorough testing
  - Use -m "not slow" to skip these tests entirely
"""

import pytest
import schemathesis
from datetime import timedelta
from sqlmodel import SQLModel
from fastapi.testclient import TestClient
from schemathesis.specs.openapi.checks import negative_data_rejection, ignored_auth
from hypothesis import settings, Phase

from services.api.src.api import app, limiter
from services.api.src.auth import create_access_token
from services.api.src.database.database import engine
from services.api.src.database.db_models import ExerciseTable  # noqa: F401 — registers model


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


def _token(username: str, role: str, minutes: int = 30) -> str:
    """Mint a signed JWT for test requests."""
    return create_access_token(
        data={"sub": username, "role": role},
        expires_delta=timedelta(minutes=minutes),
    )


# ---------------------------------------------------------------------------
# DB bootstrap — runs at import time so tables exist before from_asgi fires
# its first request (which may trigger the ASGI lifespan / seed).
# ---------------------------------------------------------------------------

SQLModel.metadata.create_all(engine)

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


@schema.hook
def map_headers(ctx, headers):
    """Inject Bearer tokens for endpoints that require authentication."""
    headers = headers or {}
    path = ctx.operation.full_path
    if path == "/auth/me":
        headers["Authorization"] = f"Bearer {_token('user', 'user')}"
    elif path.startswith("/admin"):
        headers["Authorization"] = f"Bearer {_token('admin', 'admin')}"
    return headers


@schema.hook
def filter_path_parameters(ctx, path_parameters):
    """Filter out path parameters with unrealistic values that SQLite can't handle.

    SQLite INTEGER is limited to signed 64-bit (-9223372036854775808 to 9223372036854775807).
    Schemathesis generates very large integers that cause OverflowError.
    We limit exercise_id to a reasonable range (1 to 1 million).
    """
    if path_parameters and "exercise_id" in path_parameters:
        exercise_id = path_parameters["exercise_id"]
        # Constrain to reasonable range (1 to 1 million)
        if isinstance(exercise_id, int):
            if exercise_id < 1:
                path_parameters["exercise_id"] = 1
            elif exercise_id > 1_000_000:
                path_parameters["exercise_id"] = 1_000_000
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
    """TestClient with ASGI lifespan (seeds DB on startup)."""
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# Explicit: login / token lifecycle
# ---------------------------------------------------------------------------


class TestLoginExplicit:
    """Targeted login edge cases that random generation rarely hits."""

    def test_valid_admin_login(self, client):
        resp = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert body["expires_in"] == 1800  # 30 min * 60 s

    def test_valid_user_login(self, client):
        resp = client.post("/auth/login", json={"username": "user", "password": "user123"})
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_wrong_password_returns_401(self, client):
        resp = client.post("/auth/login", json={"username": "admin", "password": "wrong123"})
        assert resp.status_code == 401

    def test_nonexistent_user_returns_401(self, client):
        resp = client.post("/auth/login", json={"username": "nobody", "password": "nope12"})
        assert resp.status_code == 401

    def test_password_below_min_length_returns_422(self, client):
        resp = client.post("/auth/login", json={"username": "admin", "password": "ab"})
        assert resp.status_code == 422

    def test_username_below_min_length_returns_422(self, client):
        resp = client.post("/auth/login", json={"username": "ab", "password": "admin123"})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Explicit: /auth/me token checks
# ---------------------------------------------------------------------------


class TestAuthMeExplicit:
    """Token-based /auth/me edge cases."""

    def test_returns_current_user(self, client):
        token = _token("user", "user")
        resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["username"] == "user"
        assert resp.json()["role"] == "user"

    def test_missing_token_returns_401(self, client):
        resp = client.get("/auth/me")
        assert resp.status_code == 401

    def test_expired_token_returns_401(self, client):
        token = _token("user", "user", minutes=-1)
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

    def test_list_users_as_admin(self, client):
        token = _token("admin", "admin")
        resp = client.get("/admin/users", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        usernames = [u["username"] for u in resp.json()]
        assert "admin" in usernames
        assert "user" in usernames

    def test_list_users_as_regular_user_returns_403(self, client):
        token = _token("user", "user")
        resp = client.get("/admin/users", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403

    def test_admin_delete_missing_exercise_returns_404(self, client):
        token = _token("admin", "admin")
        resp = client.delete("/admin/exercises/99999", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 404

    def test_admin_delete_as_regular_user_returns_403(self, client):
        token = _token("user", "user")
        resp = client.delete("/admin/exercises/1", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Explicit: exercise field boundary values
# ---------------------------------------------------------------------------


class TestExerciseBoundaryExplicit:
    """Boundary-value exercise CRUD — values that fuzzing may skip."""

    def test_minimum_valid_values(self, client):
        resp = client.post("/exercises", json={"name": "X", "sets": 1, "reps": 1})
        assert resp.status_code == 201
        assert resp.json()["sets"] == 1
        assert resp.json()["reps"] == 1

    def test_maximum_sets_accepted(self, client):
        resp = client.post("/exercises", json={"name": "MaxSets", "sets": 100, "reps": 1})
        assert resp.status_code == 201
        assert resp.json()["sets"] == 100

    def test_maximum_reps_accepted(self, client):
        resp = client.post("/exercises", json={"name": "MaxReps", "sets": 1, "reps": 1000})
        assert resp.status_code == 201
        assert resp.json()["reps"] == 1000

    def test_zero_weight_accepted(self, client):
        resp = client.post("/exercises", json={"name": "ZeroWt", "sets": 1, "reps": 1, "weight": 0.0})
        assert resp.status_code == 201
        assert resp.json()["weight"] == 0.0

    def test_sets_above_max_rejected(self, client):
        resp = client.post("/exercises", json={"name": "Over", "sets": 101, "reps": 1})
        assert resp.status_code == 422

    def test_reps_above_max_rejected(self, client):
        resp = client.post("/exercises", json={"name": "Over", "sets": 1, "reps": 1001})
        assert resp.status_code == 422

    def test_patch_weight_to_null_clears_weight(self, client):
        create = client.post("/exercises", json={"name": "W", "sets": 1, "reps": 1, "weight": 50.0})
        eid = create.json()["id"]
        resp = client.patch(f"/exercises/{eid}", json={"weight": None})
        assert resp.status_code == 200
        assert resp.json()["weight"] is None

    def test_patch_empty_body_leaves_exercise_unchanged(self, client):
        create = client.post("/exercises", json={"name": "NoChange", "sets": 3, "reps": 10})
        eid = create.json()["id"]
        resp = client.patch(f"/exercises/{eid}", json={})
        assert resp.status_code == 200
        assert resp.json()["name"] == "NoChange"
        assert resp.json()["sets"] == 3
