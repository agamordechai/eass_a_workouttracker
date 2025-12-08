"""Tests for the Frontend HTTP client.

Tests verify that the client correctly communicates with the API.
Uses httpx's MockTransport for isolated testing without a running server.
"""

import pytest
from typing import Generator
from unittest.mock import patch, MagicMock

import httpx

from services.frontend.src.client import (
    list_exercises,
    get_exercise,
    create_exercise,
    update_exercise,
    delete_exercise,
    _client,
)


@pytest.fixture
def mock_exercises() -> list[dict]:
    """Sample exercise data for tests.

    Returns:
        list[dict]: A list of sample exercise dictionaries.
    """
    return [
        {"id": 1, "name": "Bench Press", "sets": 3, "reps": 10, "weight": 80.0},
        {"id": 2, "name": "Pull-ups", "sets": 3, "reps": 12, "weight": None},
        {"id": 3, "name": "Squat", "sets": 4, "reps": 8, "weight": 100.0},
    ]


@pytest.fixture(autouse=True)
def clear_client_cache() -> Generator[None, None, None]:
    """Clear the LRU cache before each test.

    Ensures each test gets a fresh client instance.

    Yields:
        None: After the test completes.
    """
    _client.cache_clear()
    yield
    _client.cache_clear()


def create_mock_response(status_code: int, json_data=None) -> MagicMock:
    """Create a properly mocked httpx.Response.

    Args:
        status_code (int): HTTP status code.
        json_data: Data to return from .json() method.

    Returns:
        MagicMock: A mocked response object.
    """
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = json_data

    # Mock raise_for_status to behave correctly
    if status_code >= 400:
        response.raise_for_status.side_effect = httpx.HTTPStatusError(
            message=f"HTTP {status_code}",
            request=MagicMock(),
            response=response
        )
    else:
        response.raise_for_status.return_value = None

    return response


class TestListExercises:
    """Tests for list_exercises function."""

    def test_list_exercises_returns_list(
        self, mock_exercises: list[dict]
    ) -> None:
        """Test that list_exercises returns a list of exercises.

        Args:
            mock_exercises (list[dict]): Sample exercise data.
        """
        with patch("services.frontend.src.client._client") as mock_client_fn:
            mock_client = MagicMock()
            mock_client.get.return_value = create_mock_response(200, mock_exercises)
            mock_client_fn.return_value = mock_client

            result = list_exercises()

            assert isinstance(result, list)
            assert len(result) == 3
            assert result[0]["name"] == "Bench Press"

    def test_list_exercises_empty(self) -> None:
        """Test that list_exercises handles empty response."""
        with patch("services.frontend.src.client._client") as mock_client_fn:
            mock_client = MagicMock()
            mock_client.get.return_value = create_mock_response(200, [])
            mock_client_fn.return_value = mock_client

            result = list_exercises()

            assert result == []


class TestGetExercise:
    """Tests for get_exercise function."""

    def test_get_exercise_by_id(self, mock_exercises: list[dict]) -> None:
        """Test that get_exercise returns a specific exercise.

        Args:
            mock_exercises (list[dict]): Sample exercise data.
        """
        expected = mock_exercises[0]

        with patch("services.frontend.src.client._client") as mock_client_fn:
            mock_client = MagicMock()
            mock_client.get.return_value = create_mock_response(200, expected)
            mock_client_fn.return_value = mock_client

            result = get_exercise(1)

            assert result["id"] == 1
            assert result["name"] == "Bench Press"
            mock_client.get.assert_called_once_with("/exercises/1")

    def test_get_exercise_not_found(self) -> None:
        """Test that get_exercise raises on 404."""
        with patch("services.frontend.src.client._client") as mock_client_fn:
            mock_client = MagicMock()
            mock_client.get.return_value = create_mock_response(404, {"detail": "Exercise not found"})
            mock_client_fn.return_value = mock_client

            with pytest.raises(httpx.HTTPStatusError):
                get_exercise(9999)


class TestCreateExercise:
    """Tests for create_exercise function."""

    def test_create_exercise_with_weight(self) -> None:
        """Test creating an exercise with weight."""
        new_exercise = {"id": 4, "name": "Deadlift", "sets": 3, "reps": 5, "weight": 120.0}

        with patch("services.frontend.src.client._client") as mock_client_fn:
            mock_client = MagicMock()
            mock_client.post.return_value = create_mock_response(201, new_exercise)
            mock_client_fn.return_value = mock_client

            result = create_exercise(name="Deadlift", sets=3, reps=5, weight=120.0)

            assert result["name"] == "Deadlift"
            assert result["weight"] == 120.0

    def test_create_exercise_bodyweight(self) -> None:
        """Test creating a bodyweight exercise (no weight)."""
        new_exercise = {"id": 5, "name": "Push-ups", "sets": 3, "reps": 20, "weight": None}

        with patch("services.frontend.src.client._client") as mock_client_fn:
            mock_client = MagicMock()
            mock_client.post.return_value = create_mock_response(201, new_exercise)
            mock_client_fn.return_value = mock_client

            result = create_exercise(name="Push-ups", sets=3, reps=20)

            assert result["name"] == "Push-ups"
            assert result["weight"] is None


class TestUpdateExercise:
    """Tests for update_exercise function."""

    def test_update_exercise_partial(self) -> None:
        """Test partial update of an exercise."""
        updated = {"id": 1, "name": "Bench Press", "sets": 4, "reps": 10, "weight": 85.0}

        with patch("services.frontend.src.client._client") as mock_client_fn:
            mock_client = MagicMock()
            mock_client.patch.return_value = create_mock_response(200, updated)
            mock_client_fn.return_value = mock_client

            result = update_exercise(1, sets=4, weight=85.0)

            assert result["sets"] == 4
            assert result["weight"] == 85.0

    def test_update_exercise_to_bodyweight(self) -> None:
        """Test updating an exercise to bodyweight (weight=None)."""
        updated = {"id": 1, "name": "Bench Press", "sets": 3, "reps": 10, "weight": None}

        with patch("services.frontend.src.client._client") as mock_client_fn:
            mock_client = MagicMock()
            mock_client.patch.return_value = create_mock_response(200, updated)
            mock_client_fn.return_value = mock_client

            result = update_exercise(1, weight=None)

            assert result["weight"] is None


class TestDeleteExercise:
    """Tests for delete_exercise function."""

    def test_delete_exercise_success(self) -> None:
        """Test successful deletion of an exercise."""
        with patch("services.frontend.src.client._client") as mock_client_fn:
            mock_client = MagicMock()
            mock_client.delete.return_value = create_mock_response(204, None)
            mock_client_fn.return_value = mock_client

            # Should not raise
            delete_exercise(1)

            mock_client.delete.assert_called_once_with("/exercises/1")

    def test_delete_exercise_not_found(self) -> None:
        """Test deleting a non-existent exercise raises error."""
        with patch("services.frontend.src.client._client") as mock_client_fn:
            mock_client = MagicMock()
            mock_client.delete.return_value = create_mock_response(404, {"detail": "Exercise not found"})
            mock_client_fn.return_value = mock_client

            with pytest.raises(httpx.HTTPStatusError):
                delete_exercise(9999)

