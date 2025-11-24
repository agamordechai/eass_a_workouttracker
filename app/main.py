from fastapi import FastAPI, HTTPException
from typing import List
from app.models import Exercise, ExerciseResponse, ExerciseEditRequest
from app.repository import get_all_exercises, get_exercise_by_id, create_exercise, edit_exercise, delete_exercise

app = FastAPI(
    title='Workout Tracker',
    description='A simple workout tracker app',
    version='0.1.0'
)

@app.get('/')
def read_root():
    return {'message': 'Welcome to the Workout Tracker API'}

@app.get('/exercises', response_model=List[ExerciseResponse])
def read_exercises():
    """Get all exercises"""
    return get_all_exercises()

@app.get('/exercises/{exercise_id}', response_model=ExerciseResponse)
def read_exercise(exercise_id: int):
    """Get a specific exercise by ID"""
    exercise = get_exercise_by_id(exercise_id)
    if not exercise:
        raise HTTPException(status_code=404, detail='Exercise not found')
    return exercise

@app.post('/exercises', response_model=ExerciseResponse, status_code=201)
def add_exercise(exercise: Exercise):
    """Create a new exercise"""
    new_exercise = create_exercise(
        name=exercise.name,
        sets=exercise.sets,
        reps=exercise.reps,
        weight=exercise.weight
    )
    return new_exercise

@app.patch('/exercises/{exercise_id}', response_model=ExerciseResponse)
def edit_exercise_endpoint(exercise_id: int, exercise_edit: ExerciseEditRequest):
    """Update any attributes of a specific exercise"""
    exercise = edit_exercise(
        exercise_id,
        name=exercise_edit.name,
        sets=exercise_edit.sets,
        reps=exercise_edit.reps,
        weight=exercise_edit.weight
    )
    if not exercise:
        raise HTTPException(status_code=404, detail='Exercise not found')
    return exercise

@app.delete('/exercises/{exercise_id}', status_code=204)
def delete_exercise_endpoint(exercise_id: int):
    """Delete a specific exercise"""
    success = delete_exercise(exercise_id)
    if not success:
        raise HTTPException(status_code=404, detail='Exercise not found')
    return None

