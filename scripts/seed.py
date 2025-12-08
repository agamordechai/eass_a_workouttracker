"""
Seed script to populate the workout tracker database with sample exercises.

This script can be run independently to reset the database with fresh sample data.
"""

import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.repository import get_db_connection, init_db


def seed_database() -> None:
    """Seed the database with sample workout exercises.

    Initializes the database, clears any existing data, and populates it with
    a predefined set of sample exercises including various workout types.

    Returns:
        None
    """
    print("Initializing database...")
    init_db()

    print("Clearing existing data...")
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM exercises')

    print("Seeding sample exercises...")
    seed_data = [
        ('Bench Press', 3, 10, 95.0),
        ('Shoulder Press', 3, 10, 22.5),
        ('Tricep Curl', 3, 10, 42.5),
        ('Pull Ups', 3, 8, 90.0),
        ('Squats', 3, 8, 60.0),
        ('Hip Thrust', 3, 8, 45.0),
        ('Deadlift', 5, 5, 135.0),
        ('Barbell Row', 4, 8, 85.0),
        ('Leg Press', 3, 12, 180.0),
        ('Lat Pulldown', 3, 10, 70.0),
    ]

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.executemany(
            'INSERT INTO exercises (name, sets, reps, weight) VALUES (?, ?, ?, ?)',
            seed_data
        )

    print(f"✓ Successfully seeded {len(seed_data)} exercises")


if __name__ == '__main__':
    seed_database()

