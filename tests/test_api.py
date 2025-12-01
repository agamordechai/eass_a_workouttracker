import pytest
import os
from fastapi.testclient import TestClient
from app.main import app
from app import repository


@pytest.fixture(scope='function')
def test_db():
    """Create a test database for each test"""
    # Use a test-specific database
    test_db_path = 'test_workout_tracker.db'
    original_db_path = repository.DB_PATH
    repository.DB_PATH = test_db_path

    # Initialize test database
    repository.init_db()

    yield

    # Cleanup: restore original DB path and remove test database
    repository.DB_PATH = original_db_path
    if os.path.exists(test_db_path):
        os.remove(test_db_path)


@pytest.fixture(scope='function')
def client(test_db):
    """Create a test client with isolated database"""
    return TestClient(app)


def test_read_root(client):
    """Test the root endpoint"""
    response = client.get('/')
    assert response.status_code == 200
    assert response.json() == {'message': 'Welcome to the Workout Tracker API'}


def test_read_exercises(client):
    """Test getting all exercises"""
    response = client.get('/exercises')
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert 'id' in data[0]
    assert 'name' in data[0]
    assert 'sets' in data[0]
    assert 'reps' in data[0]


def test_read_exercise_by_id(client):
    """Test getting a specific exercise"""
    response = client.get('/exercises/1')
    assert response.status_code == 200
    data = response.json()
    assert data['id'] == 1
    assert 'name' in data


def test_read_exercise_not_found(client):
    """Test getting a non-existent exercise"""
    response = client.get('/exercises/9999')
    assert response.status_code == 404
    assert response.json()['detail'] == 'Exercise not found'


def test_create_exercise(client):
    """Test creating a new exercise"""
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


def test_create_exercise_validation_error(client):
    """Test creating an exercise with invalid data"""
    invalid_exercise = {
        'name': 'Invalid',
        'sets': 'not_a_number',
        'reps': 10
    }
    response = client.post('/exercises', json=invalid_exercise)
    assert response.status_code == 422


def test_edit_exercise(client):
    """Test updating an exercise"""
    update_data = {
        'sets': 4,
        'reps': 12
    }
    response = client.patch('/exercises/1', json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data['sets'] == 4
    assert data['reps'] == 12


def test_edit_exercise_not_found(client):
    """Test updating a non-existent exercise"""
    update_data = {'sets': 5}
    response = client.patch('/exercises/9999', json=update_data)
    assert response.status_code == 404


def test_delete_exercise(client):
    """Test deleting an exercise"""
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


def test_delete_exercise_not_found(client):
    """Test deleting a non-existent exercise"""
    response = client.delete('/exercises/9999')
    assert response.status_code == 404

