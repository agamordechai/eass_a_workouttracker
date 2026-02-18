"""Tests for the Workout Tracker API endpoints.

Uses pytest fixtures for test isolation with a separate test database.
All exercise tests use JWT tokens tied to a test user in the database.
"""

import os
from collections.abc import Generator
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from services.api.src.api import app, limiter
from services.api.src.auth import create_access_token
from services.api.src.database.database import get_session
from services.api.src.database.db_models import UserTable

# Disable rate limiter for tests (requires Redis which may not be available)
limiter.enabled = False


@pytest.fixture(scope="function")
def test_db() -> Generator[None, None, None]:
    """Create a test database for each test.

    Yields:
        The fixture sets up the test database environment and cleans up after.
    """
    test_db_path = "test_workout_tracker.db"
    yield
    if os.path.exists(test_db_path):
        os.remove(test_db_path)


def _ensure_test_user(session: Session) -> UserTable:
    """Ensure the system user (id=1) exists for test data."""
    user = session.get(UserTable, 1)
    if user is None:
        user = UserTable(
            id=1,
            google_id="system",
            email="system@workout.local",
            name="System User",
            role="admin",
        )
        session.add(user)
        session.commit()
        session.refresh(user)
    return user


def _ensure_regular_user(session: Session) -> UserTable:
    """Ensure a regular test user (id=2) exists."""
    user = session.get(UserTable, 2)
    if user is None:
        user = UserTable(
            id=2,
            google_id="test-google-2",
            email="testuser@example.com",
            name="Test User",
            role="user",
        )
        session.add(user)
        session.commit()
        session.refresh(user)
    return user


@pytest.fixture(scope="function")
def client(test_db: Generator[None, None, None]) -> TestClient:
    """Create a test client with isolated database.

    Args:
        test_db: The test database fixture that provides an isolated database.

    Returns:
        A FastAPI test client configured with the test database.
    """
    # Ensure test users exist
    with next(get_session()) as session:
        _ensure_test_user(session)
        _ensure_regular_user(session)
    return TestClient(app)


@pytest.fixture(scope="function")
def auth_headers() -> dict[str, str]:
    """Get authentication headers for the test user (id=2).

    Returns:
        Authorization headers with Bearer token.
    """
    token = create_access_token(
        data={"sub": "2", "role": "user"},
        expires_delta=timedelta(minutes=30),
    )
    return {"Authorization": f"Bearer {token}"}


def test_read_root(client: TestClient) -> None:
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "Welcome to the Workout Tracker API" in data["message"]


def test_read_exercises(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Test getting all exercises with pagination (requires auth)."""
    response = client.get("/exercises", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, dict)
    assert "page" in data
    assert "page_size" in data
    assert "total" in data
    assert "items" in data
    assert isinstance(data["items"], list)


def test_read_exercises_requires_auth(client: TestClient) -> None:
    """Test that reading exercises requires authentication."""
    response = client.get("/exercises")
    assert response.status_code == 401


def test_read_exercise_by_id(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Test getting a specific exercise."""
    new_exercise = {"name": "Test Exercise", "sets": 3, "reps": 10}
    create_response = client.post("/exercises", json=new_exercise, headers=auth_headers)
    exercise_id = create_response.json()["id"]

    response = client.get(f"/exercises/{exercise_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == exercise_id
    assert "name" in data


def test_read_exercise_not_found(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Test getting a non-existent exercise."""
    response = client.get("/exercises/9999", headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Exercise not found"


def test_create_exercise(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Test creating a new exercise."""
    new_exercise = {"name": "Deadlift", "sets": 5, "reps": 5, "weight": 135.0}
    response = client.post("/exercises", json=new_exercise, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Deadlift"
    assert data["sets"] == 5
    assert data["reps"] == 5
    assert data["weight"] == 135.0
    assert "id" in data


def test_create_exercise_requires_auth(client: TestClient) -> None:
    """Test that creating an exercise requires authentication."""
    new_exercise = {"name": "Unauthorized Exercise", "sets": 3, "reps": 10}
    response = client.post("/exercises", json=new_exercise)
    assert response.status_code == 401


def test_create_exercise_validation_error(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Test creating an exercise with invalid data."""
    invalid_exercise = {"name": "Invalid", "sets": "not_a_number", "reps": 10}
    response = client.post("/exercises", json=invalid_exercise, headers=auth_headers)
    assert response.status_code == 422


def test_edit_exercise(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Test updating an exercise."""
    new_exercise = {"name": "Exercise to Update", "sets": 3, "reps": 10}
    create_response = client.post("/exercises", json=new_exercise, headers=auth_headers)
    exercise_id = create_response.json()["id"]

    update_data = {"sets": 4, "reps": 12}
    response = client.patch(f"/exercises/{exercise_id}", json=update_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["sets"] == 4
    assert data["reps"] == 12


def test_edit_exercise_not_found(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Test updating a non-existent exercise."""
    update_data = {"sets": 5}
    response = client.patch("/exercises/9999", json=update_data, headers=auth_headers)
    assert response.status_code == 404


def test_update_exercise_requires_auth(client: TestClient) -> None:
    """Test that updating an exercise requires authentication."""
    response = client.patch("/exercises/1", json={"sets": 5})
    assert response.status_code == 401


def test_delete_exercise(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Test deleting an exercise."""
    new_exercise = {"name": "Temp Exercise", "sets": 3, "reps": 10}
    create_response = client.post("/exercises", json=new_exercise, headers=auth_headers)
    exercise_id = create_response.json()["id"]

    response = client.delete(f"/exercises/{exercise_id}", headers=auth_headers)
    assert response.status_code == 204

    get_response = client.get(f"/exercises/{exercise_id}", headers=auth_headers)
    assert get_response.status_code == 404


def test_delete_exercise_not_found(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Test deleting a non-existent exercise."""
    response = client.delete("/exercises/9999", headers=auth_headers)
    assert response.status_code == 404


def test_delete_exercise_requires_auth(client: TestClient) -> None:
    """Test that deleting an exercise requires authentication."""
    response = client.delete("/exercises/1")
    assert response.status_code == 401


def test_health_check(client: TestClient) -> None:
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "timestamp" in data
    assert "database" in data
    assert data["database"]["status"] == "connected"


def test_create_exercise_invalid_name_empty(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Test creating an exercise with empty name fails validation."""
    invalid_exercise = {"name": "", "sets": 3, "reps": 10}
    response = client.post("/exercises", json=invalid_exercise, headers=auth_headers)
    assert response.status_code == 422


def test_create_exercise_invalid_sets_zero(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Test creating an exercise with zero sets fails validation."""
    invalid_exercise = {"name": "Test Exercise", "sets": 0, "reps": 10}
    response = client.post("/exercises", json=invalid_exercise, headers=auth_headers)
    assert response.status_code == 422


def test_create_exercise_invalid_negative_weight(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Test creating an exercise with negative weight fails validation."""
    invalid_exercise = {"name": "Test Exercise", "sets": 3, "reps": 10, "weight": -5.0}
    response = client.post("/exercises", json=invalid_exercise, headers=auth_headers)
    assert response.status_code == 422


# ============ Workout Day Split Feature Tests ============


def test_create_exercise_with_workout_day(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Test creating an exercise with a specific workout day."""
    new_exercise = {"name": "Bench Press", "sets": 4, "reps": 8, "weight": 80.0, "workout_day": "A"}
    response = client.post("/exercises", json=new_exercise, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["workout_day"] == "A"


def test_create_exercise_default_workout_day(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Test that exercises get default workout day when not specified."""
    new_exercise = {"name": "Default Day Exercise", "sets": 3, "reps": 10}
    response = client.post("/exercises", json=new_exercise, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert "workout_day" in data
    assert data["workout_day"] == "A"


def test_create_exercise_with_different_workout_days(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Test creating exercises with different workout days (A-G split)."""
    workout_days = ["A", "B", "C", "D", "E", "F", "G"]

    for day in workout_days:
        exercise = {"name": f"Exercise Day {day}", "sets": 3, "reps": 10, "workout_day": day}
        response = client.post("/exercises", json=exercise, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["workout_day"] == day


def test_create_exercise_with_none_workout_day(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Test creating a daily exercise (workout_day = 'None')."""
    new_exercise = {"name": "Daily Stretching", "sets": 1, "reps": 10, "workout_day": "None"}
    response = client.post("/exercises", json=new_exercise, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["workout_day"] == "None"


def test_update_exercise_workout_day(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Test updating an exercise's workout day."""
    new_exercise = {"name": "Movable Exercise", "sets": 3, "reps": 10, "workout_day": "A"}
    create_response = client.post("/exercises", json=new_exercise, headers=auth_headers)
    exercise_id = create_response.json()["id"]
    assert create_response.json()["workout_day"] == "A"

    update_response = client.patch(f"/exercises/{exercise_id}", json={"workout_day": "B"}, headers=auth_headers)
    assert update_response.status_code == 200
    assert update_response.json()["workout_day"] == "B"


def test_exercise_response_includes_workout_day(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Test that exercise list includes workout_day field."""
    new_exercise = {"name": "Test Exercise", "sets": 3, "reps": 10, "workout_day": "A"}
    client.post("/exercises", json=new_exercise, headers=auth_headers)

    response = client.get("/exercises", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    assert "items" in data
    assert len(data["items"]) > 0

    for exercise in data["items"]:
        assert "workout_day" in exercise


def test_get_single_exercise_includes_workout_day(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Test that getting a single exercise includes workout_day."""
    new_exercise = {"name": "Single Fetch Test", "sets": 3, "reps": 10, "workout_day": "C"}
    create_response = client.post("/exercises", json=new_exercise, headers=auth_headers)
    exercise_id = create_response.json()["id"]

    response = client.get(f"/exercises/{exercise_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["workout_day"] == "C"
