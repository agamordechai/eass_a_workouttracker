"""Database repository for Workout Tracker API.

Provides CRUD operations for exercises using SQLite.
"""
import sqlite3
from typing import List, Dict, Optional, Generator, Any
from contextlib import contextmanager

from services.api.src.database.config import get_settings


@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """Context manager for database connections with automatic commit/rollback.

    Yields:
        sqlite3.Connection: A database connection with row_factory set to sqlite3.Row.
            The connection automatically commits on success or rolls back on exception.
    """
    settings = get_settings()
    conn = sqlite3.connect(
        str(settings.db.path),
        timeout=settings.db.timeout
    )
    conn.row_factory = sqlite3.Row

    # Enable SQL echo if configured (for debugging)
    if settings.db.echo_sql:
        conn.set_trace_callback(print)

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Initialize the database with the exercises table and seed data if empty.

    Creates the exercises table if it doesn't exist and populates it with
    sample workout data if the table is empty.

    Returns:
        None
    """
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
            # Seed with initial data (mix of weighted and bodyweight exercises)
            seed_data = [
                ('Bench Press', 3, 10, 95),
                ('Shoulder Press', 3, 10, 22.5),
                ('Tricep curl', 3, 10, 42.5),
                ('Pull ups', 3, 8, None),  # Bodyweight
                ('Push ups', 3, 15, None),  # Bodyweight
                ('Squats', 3, 8, 60),
                ('Hip Thrust', 3, 8, 45),
                ('Plank', 3, 60, None),  # Bodyweight (reps = seconds)
            ]
            cursor.executemany(
                'INSERT INTO exercises (name, sets, reps, weight) VALUES (?, ?, ?, ?)',
                seed_data
            )


# Initialize database on module import
init_db()


def get_all_exercises() -> List[Dict]:
    """Retrieve all exercises from the database.

    Returns:
        List[Dict]: A list of dictionaries, each containing exercise details
            (id, name, sets, reps, weight).
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, sets, reps, weight FROM exercises')
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_exercise_by_id(exercise_id: int) -> Optional[Dict]:
    """Retrieve a specific exercise by ID from the database.

    Args:
        exercise_id (int): The unique identifier of the exercise to retrieve.

    Returns:
        Optional[Dict]: A dictionary containing exercise details (id, name, sets, reps, weight)
            if found, None otherwise.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, name, sets, reps, weight FROM exercises WHERE id = ?',
            (exercise_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def create_exercise(name: str, sets: int, reps: int, weight: Optional[float] = None) -> Dict:
    """Create a new exercise in the database.

    Args:
        name (str): The name of the exercise.
        sets (int): The number of sets to perform.
        reps (int): The number of repetitions per set.
        weight (Optional[float], optional): The weight used in the exercise. Defaults to None.

    Returns:
        Dict: A dictionary containing the newly created exercise details including
            the auto-generated id.
    """
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
                  reps: Optional[int] = None, weight: Optional[float] = None,
                  update_weight: bool = False) -> Optional[Dict[str, Any]]:
    """Update any attributes of an exercise in the database.

    Only the provided fields will be updated; None values are ignored except for weight
    when update_weight is True (allows setting weight to None for bodyweight exercises).

    Args:
        exercise_id (int): The unique identifier of the exercise to update.
        name (Optional[str], optional): The new name for the exercise. Defaults to None.
        sets (Optional[int], optional): The new number of sets. Defaults to None.
        reps (Optional[int], optional): The new number of repetitions. Defaults to None.
        weight (Optional[float], optional): The new weight value. Defaults to None.
        update_weight (bool, optional): If True, updates weight even if None. Defaults to False.

    Returns:
        Optional[Dict]: A dictionary containing the updated exercise details if the
            exercise exists, None otherwise.
    """
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
    # Include weight update if it's not None OR if update_weight flag is True
    if weight is not None or update_weight:
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
    """Delete an exercise by ID from the database.

    Args:
        exercise_id (int): The unique identifier of the exercise to delete.

    Returns:
        bool: True if the exercise was successfully deleted, False if the exercise
            was not found.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM exercises WHERE id = ?', (exercise_id,))
        return cursor.rowcount > 0
