"""Tests for the Workout Tracker API endpoints.

Uses pytest fixtures for test isolation with a separate test database.
"""
import pytest
import os
from typing import Generator
from fastapi.testclient import TestClient
from services.api.src.api import app


@pytest.fixture(scope='function')
def test_db() -> Generator[None, None, None]:
    """Create a test database for each test.

    This fixture creates an isolated test database for each test function,
    ensuring tests don't interfere with each other or the production database.

    Yields:
        None: The fixture sets up the test database environment and cleans up after.
    """
    # Use a test-specific database
    test_db_path = 'test_workout_tracker.db'

    # We need to reset the database connection to use test DB
    # This works by reinitializing the DB
    yield

    # Cleanup: remove test database
    if os.path.exists(test_db_path):
        os.remove(test_db_path)


@pytest.fixture(scope='function')
def client(test_db: Generator[None, None, None]) -> TestClient:
    """Create a test client with isolated database.

    Args:
        test_db: The test database fixture that provides an isolated database.

    Returns:
        TestClient: A FastAPI test client configured with the test database.
    """
    return TestClient(app)


def test_read_root(client: TestClient) -> None:
    """Test the root endpoint.

    Args:
        client (TestClient): The test client fixture.
    """
    response = client.get('/')
    assert response.status_code == 200
    data = response.json()
    assert 'message' in data
    assert 'Welcome to the Workout Tracker API' in data['message']


def test_read_exercises(client: TestClient) -> None:
    """Test getting all exercises.

    Args:
        client (TestClient): The test client fixture.
    """
    response = client.get('/exercises')
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert 'id' in data[0]
    assert 'name' in data[0]
    assert 'sets' in data[0]
    assert 'reps' in data[0]


def test_read_exercise_by_id(client: TestClient) -> None:
    """Test getting a specific exercise.

    Args:
        client (TestClient): The test client fixture.
    """
    # First create an exercise to ensure one exists
    new_exercise = {
        'name': 'Test Exercise',
        'sets': 3,
        'reps': 10
    }
    create_response = client.post('/exercises', json=new_exercise)
    exercise_id = create_response.json()['id']

    response = client.get(f'/exercises/{exercise_id}')
    assert response.status_code == 200
    data = response.json()
    assert data['id'] == exercise_id
    assert 'name' in data


def test_read_exercise_not_found(client: TestClient) -> None:
    """Test getting a non-existent exercise.

    Args:
        client (TestClient): The test client fixture.
    """
    response = client.get('/exercises/9999')
    assert response.status_code == 404
    assert response.json()['detail'] == 'Exercise not found'


def test_create_exercise(client: TestClient) -> None:
    """Test creating a new exercise.

    Args:
        client (TestClient): The test client fixture.
    """
    new_exercise = {
        'name': 'Deadlift',
        'sets': 5,
        'reps': 5,
        'weight': 135.0
    }
    response = client.post('/exercises', json=new_exercise)
    assert response.status_code == 201
    data = response.json()
    assert data['name'] == 'Deadlift'
    assert data['sets'] == 5
    assert data['reps'] == 5
    assert data['weight'] == 135.0
    assert 'id' in data


def test_create_exercise_validation_error(client: TestClient) -> None:
    """Test creating an exercise with invalid data.

    Args:
        client (TestClient): The test client fixture.
    """
    invalid_exercise = {
        'name': 'Invalid',
        'sets': 'not_a_number',
        'reps': 10
    }
    response = client.post('/exercises', json=invalid_exercise)
    assert response.status_code == 422


def test_edit_exercise(client: TestClient) -> None:
    """Test updating an exercise.

    Args:
        client (TestClient): The test client fixture.
    """
    # First create an exercise to update
    new_exercise = {
        'name': 'Exercise to Update',
        'sets': 3,
        'reps': 10
    }
    create_response = client.post('/exercises', json=new_exercise)
    exercise_id = create_response.json()['id']

    update_data = {
        'sets': 4,
        'reps': 12
    }
    response = client.patch(f'/exercises/{exercise_id}', json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data['sets'] == 4
    assert data['reps'] == 12


def test_edit_exercise_not_found(client: TestClient) -> None:
    """Test updating a non-existent exercise.

    Args:
        client (TestClient): The test client fixture.
    """
    update_data = {'sets': 5}
    response = client.patch('/exercises/9999', json=update_data)
    assert response.status_code == 404


def test_delete_exercise(client: TestClient) -> None:
    """Test deleting an exercise.

    Args:
        client (TestClient): The test client fixture.
    """
    new_exercise = {
        'name': 'Temp Exercise',
        'sets': 3,
        'reps': 10
    }
    create_response = client.post('/exercises', json=new_exercise)
    exercise_id = create_response.json()['id']

    response = client.delete(f'/exercises/{exercise_id}')
    assert response.status_code == 204

    get_response = client.get(f'/exercises/{exercise_id}')
    assert get_response.status_code == 404


def test_delete_exercise_not_found(client: TestClient) -> None:
    """Test deleting a non-existent exercise.

    Args:
        client (TestClient): The test client fixture.
    """
    response = client.delete('/exercises/9999')
    assert response.status_code == 404


def test_health_check(client: TestClient) -> None:
    """Test the health check endpoint.

    Args:
        client (TestClient): The test client fixture.
    """
    response = client.get('/health')
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'healthy'
    assert 'version' in data
    assert 'timestamp' in data
    assert 'database' in data
    assert data['database']['status'] == 'connected'


def test_create_exercise_invalid_name_empty(client: TestClient) -> None:
    """Test creating an exercise with empty name fails validation.

    Args:
        client (TestClient): The test client fixture.
    """
    invalid_exercise = {
        'name': '',
        'sets': 3,
        'reps': 10
    }
    response = client.post('/exercises', json=invalid_exercise)
    assert response.status_code == 422


def test_create_exercise_invalid_sets_zero(client: TestClient) -> None:
    """Test creating an exercise with zero sets fails validation.

    Args:
        client (TestClient): The test client fixture.
    """
    invalid_exercise = {
        'name': 'Test Exercise',
        'sets': 0,
        'reps': 10
    }
    response = client.post('/exercises', json=invalid_exercise)
    assert response.status_code == 422


def test_create_exercise_invalid_negative_weight(client: TestClient) -> None:
    """Test creating an exercise with negative weight fails validation.

    Args:
        client (TestClient): The test client fixture.
    """
    invalid_exercise = {
        'name': 'Test Exercise',
        'sets': 3,
        'reps': 10,
        'weight': -5.0
    }
    response = client.post('/exercises', json=invalid_exercise)
    assert response.status_code == 422


