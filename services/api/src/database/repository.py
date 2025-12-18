"""Database repository for Workout Tracker API.

Provides CRUD operations for exercises using PostgreSQL or SQLite.
"""
import sqlite3
from typing import List, Dict, Optional, Generator, Any
from contextlib import contextmanager

from services.api.src.database.config import get_settings

# Try to import psycopg2 for PostgreSQL support
try:
    import psycopg2
    import psycopg2.extras
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False


@contextmanager
def get_db_connection() -> Generator[Any, None, None]:
    """Context manager for database connections with automatic commit/rollback.

    Supports both PostgreSQL and SQLite based on configuration.

    Yields:
        Connection: A database connection.
            The connection automatically commits on success or rolls back on exception.
    """
    settings = get_settings()

    if settings.db.is_postgres:
        if not HAS_PSYCOPG2:
            raise ImportError("psycopg2 is required for PostgreSQL support. Install with: pip install psycopg2-binary")

        conn = psycopg2.connect(settings.db.url)
        conn.autocommit = False

        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    else:
        # SQLite fallback
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


def _row_to_dict(row, cursor, is_postgres: bool) -> Dict:
    """Convert a database row to a dictionary."""
    if is_postgres:
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, row))
    else:
        return dict(row)


def init_db() -> None:
    """Initialize the database with the exercises table and seed data if empty.

    Creates the exercises table if it doesn't exist and populates it with
    sample workout data if the table is empty.

    Returns:
        None
    """
    settings = get_settings()
    is_postgres = settings.db.is_postgres

    with get_db_connection() as conn:
        cursor = conn.cursor()

        if is_postgres:
            # PostgreSQL syntax
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS exercises (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    sets INTEGER NOT NULL,
                    reps INTEGER NOT NULL,
                    weight REAL
                )
            ''')
        else:
            # SQLite syntax
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

            if is_postgres:
                cursor.executemany(
                    'INSERT INTO exercises (name, sets, reps, weight) VALUES (%s, %s, %s, %s)',
                    seed_data
                )
            else:
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
    settings = get_settings()
    is_postgres = settings.db.is_postgres

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, sets, reps, weight FROM exercises')
        rows = cursor.fetchall()
        return [_row_to_dict(row, cursor, is_postgres) for row in rows]


def get_exercise_by_id(exercise_id: int) -> Optional[Dict]:
    """Retrieve a specific exercise by ID from the database.

    Args:
        exercise_id (int): The unique identifier of the exercise to retrieve.

    Returns:
        Optional[Dict]: A dictionary containing exercise details (id, name, sets, reps, weight)
            if found, None otherwise.
    """
    settings = get_settings()
    is_postgres = settings.db.is_postgres

    with get_db_connection() as conn:
        cursor = conn.cursor()

        if is_postgres:
            cursor.execute(
                'SELECT id, name, sets, reps, weight FROM exercises WHERE id = %s',
                (exercise_id,)
            )
        else:
            cursor.execute(
                'SELECT id, name, sets, reps, weight FROM exercises WHERE id = ?',
                (exercise_id,)
            )

        row = cursor.fetchone()
        return _row_to_dict(row, cursor, is_postgres) if row else None


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
    settings = get_settings()
    is_postgres = settings.db.is_postgres

    with get_db_connection() as conn:
        cursor = conn.cursor()

        if is_postgres:
            cursor.execute(
                'INSERT INTO exercises (name, sets, reps, weight) VALUES (%s, %s, %s, %s) RETURNING id',
                (name, sets, reps, weight)
            )
            exercise_id = cursor.fetchone()[0]
        else:
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
    settings = get_settings()
    is_postgres = settings.db.is_postgres
    placeholder = '%s' if is_postgres else '?'

    # First check if exercise exists
    exercise = get_exercise_by_id(exercise_id)
    if not exercise:
        return None

    # Build dynamic UPDATE query based on provided fields
    updates = []
    params = []

    if name is not None:
        updates.append(f'name = {placeholder}')
        params.append(name)
    if sets is not None:
        updates.append(f'sets = {placeholder}')
        params.append(sets)
    if reps is not None:
        updates.append(f'reps = {placeholder}')
        params.append(reps)
    # Include weight update if it's not None OR if update_weight flag is True
    if weight is not None or update_weight:
        updates.append(f'weight = {placeholder}')
        params.append(weight)

    if not updates:
        return exercise

    params.append(exercise_id)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = f'UPDATE exercises SET {", ".join(updates)} WHERE id = {placeholder}'
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
    settings = get_settings()
    is_postgres = settings.db.is_postgres

    with get_db_connection() as conn:
        cursor = conn.cursor()
        if is_postgres:
            cursor.execute('DELETE FROM exercises WHERE id = %s', (exercise_id,))
        else:
            cursor.execute('DELETE FROM exercises WHERE id = ?', (exercise_id,))
        return cursor.rowcount > 0
