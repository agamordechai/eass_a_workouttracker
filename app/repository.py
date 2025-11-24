from typing import List, Dict, Optional

# In-memory storage for exercises
exercises_db: List[Dict] = [
    {'id': 1, 'name': 'Bench Press', 'sets': 3, 'reps': 10, 'weight': 95},
    {'id': 2, 'name': 'Shoulder Press', 'sets': 3, 'reps': 10, 'weight': 22.5},
    {'id': 3, 'name': 'Tricep curl', 'sets': 3, 'reps': 10, 'weight': 42.5},
    {'id': 4, 'name': 'Pull ups', 'sets': 3, 'reps': 8, 'weight': 90},
    {'id': 5, 'name': 'Squats', 'sets': 3, 'reps': 8, 'weight': 60},
    {'id': 6, 'name': 'Hip Thrust', 'sets': 3, 'reps': 8, 'weight': 45},
]
next_id = 7

def get_all_exercises() -> List[Dict]:
    """Retrieve all exercises"""
    return exercises_db

def get_exercise_by_id(exercise_id: int) -> Optional[Dict]:
    """Retrieve a specific exercise by ID"""
    for exercise in exercises_db:
        if exercise['id'] == exercise_id:
            return exercise
    return None

def create_exercise(name: str, sets: int, reps: int, weight: Optional[float] = None) -> Dict:
    """Create a new exercise"""
    global next_id
    new_exercise = {
        'id': next_id,
        'name': name,
        'sets': sets,
        'reps': reps,
        'weight': weight
    }
    exercises_db.append(new_exercise)
    next_id += 1
    return new_exercise

def edit_exercise(exercise_id: int, name: Optional[str] = None, sets: Optional[int] = None,
                   reps: Optional[int] = None, weight: Optional[float] = None) -> Optional[Dict]:
    """Update any attributes of an exercise"""
    exercise = get_exercise_by_id(exercise_id)
    if not exercise:
        return None

    if name is not None:
        exercise['name'] = name
    if sets is not None:
        exercise['sets'] = sets
    if reps is not None:
        exercise['reps'] = reps
    if weight is not None:
        exercise['weight'] = weight

    return exercise

def delete_exercise(exercise_id: int) -> bool:
    """Delete an exercise by ID"""
    exercise = get_exercise_by_id(exercise_id)
    if not exercise:
        return False
    exercises_db.remove(exercise)
    return True

