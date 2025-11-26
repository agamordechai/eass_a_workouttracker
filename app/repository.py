import sqlite3
from typing import List, Dict, Optional
from contextlib import contextmanager
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'workout_tracker.db')

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    """Initialize the database with the exercises table"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exercises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                sets INTEGER NOT NULL,
                reps INTEGER NOT NULL,
                weight REAL
            )
        ''')

        # Check if we need to seed data
        cursor.execute('SELECT COUNT(*) FROM exercises')
        count = cursor.fetchone()[0]

        if count == 0:
            # Seed with initial data
            seed_data = [
                ('Bench Press', 3, 10, 95),
                ('Shoulder Press', 3, 10, 22.5),
                ('Tricep curl', 3, 10, 42.5),
                ('Pull ups', 3, 8, 90),
                ('Squats', 3, 8, 60),
                ('Hip Thrust', 3, 8, 45),
            ]
            cursor.executemany(
                'INSERT INTO exercises (name, sets, reps, weight) VALUES (?, ?, ?, ?)',
                seed_data
            )

# Initialize database on module import
init_db()

def get_all_exercises() -> List[Dict]:
    """Retrieve all exercises"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, sets, reps, weight FROM exercises')
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_exercise_by_id(exercise_id: int) -> Optional[Dict]:
    """Retrieve a specific exercise by ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, name, sets, reps, weight FROM exercises WHERE id = ?',
            (exercise_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

def create_exercise(name: str, sets: int, reps: int, weight: Optional[float] = None) -> Dict:
    """Create a new exercise"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO exercises (name, sets, reps, weight) VALUES (?, ?, ?, ?)',
            (name, sets, reps, weight)
        )
        exercise_id = cursor.lastrowid
        return {
            'id': exercise_id,
            'name': name,
            'sets': sets,
            'reps': reps,
            'weight': weight
        }

def edit_exercise(exercise_id: int, name: Optional[str] = None, sets: Optional[int] = None,
                   reps: Optional[int] = None, weight: Optional[float] = None) -> Optional[Dict]:
    """Update any attributes of an exercise"""
    # First check if exercise exists
    exercise = get_exercise_by_id(exercise_id)
    if not exercise:
        return None

    # Build dynamic UPDATE query based on provided fields
    updates = []
    params = []

    if name is not None:
        updates.append('name = ?')
        params.append(name)
    if sets is not None:
        updates.append('sets = ?')
        params.append(sets)
    if reps is not None:
        updates.append('reps = ?')
        params.append(reps)
    if weight is not None:
        updates.append('weight = ?')
        params.append(weight)

    if not updates:
        return exercise

    params.append(exercise_id)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = f'UPDATE exercises SET {", ".join(updates)} WHERE id = ?'
        cursor.execute(query, params)

    # Return updated exercise
    return get_exercise_by_id(exercise_id)

def delete_exercise(exercise_id: int) -> bool:
    """Delete an exercise by ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM exercises WHERE id = ?', (exercise_id,))
        return cursor.rowcount > 0

