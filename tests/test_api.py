import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_read_root():
    """Test the root endpoint"""
    response = client.get('/')
    assert response.status_code == 200
    assert response.json() == {'message': 'Welcome to the Workout Tracker API'}


def test_read_exercises():
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


def test_read_exercise_by_id():
    """Test getting a specific exercise"""
    response = client.get('/exercises/1')
    assert response.status_code == 200
    data = response.json()
    assert data['id'] == 1
    assert 'name' in data


def test_read_exercise_not_found():
    """Test getting a non-existent exercise"""
    response = client.get('/exercises/9999')
    assert response.status_code == 404
    assert response.json()['detail'] == 'Exercise not found'


def test_create_exercise():
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


def test_create_exercise_validation_error():
    """Test creating an exercise with invalid data"""
    invalid_exercise = {
        'name': 'Invalid',
        'sets': 'not_a_number',
        'reps': 10
    }
    response = client.post('/exercises', json=invalid_exercise)
    assert response.status_code == 422


def test_edit_exercise():
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


def test_edit_exercise_not_found():
    """Test updating a non-existent exercise"""
    update_data = {'sets': 5}
    response = client.patch('/exercises/9999', json=update_data)
    assert response.status_code == 404


def test_delete_exercise():
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


def test_delete_exercise_not_found():
    """Test deleting a non-existent exercise"""
    response = client.delete('/exercises/9999')
    assert response.status_code == 404

