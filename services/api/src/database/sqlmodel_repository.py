"""SQLModel-based repository for Workout Tracker API.

Provides CRUD operations for exercises using SQLModel ORM.
All queries are scoped to a specific user via user_id.
"""
from __future__ import annotations
from sqlmodel import Session, select
from sqlalchemy import func

from services.api.src.database.db_models import ExerciseTable
from services.api.src.database.models import ExerciseResponse


class ExerciseRepository:
    """Repository for exercise CRUD operations using SQLModel.

    All operations are scoped to a specific user_id for data isolation.

    Attributes:
        session: SQLModel database session
    """

    def __init__(self, session: Session):
        """Initialize repository with a database session.

        Args:
            session: SQLModel session for database operations
        """
        self.session = session

    def get_all(self, user_id: int) -> list[ExerciseResponse]:
        """Retrieve all exercises for a user.

        Args:
            user_id: Owner's user ID

        Returns:
            List of all exercises belonging to the user.
        """
        statement = select(ExerciseTable).where(ExerciseTable.user_id == user_id)
        results = self.session.exec(statement).all()
        return [ExerciseResponse.model_validate(ex.model_dump()) for ex in results]

    def list_paginated(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "id",
        sort_order: str = "asc",
    ) -> tuple[list[ExerciseResponse], int]:
        """Retrieve paginated and sorted exercises for a user.

        Args:
            user_id: Owner's user ID
            page: Page number (1-indexed)
            page_size: Number of items per page
            sort_by: Column name to sort by
            sort_order: 'asc' or 'desc'

        Returns:
            Tuple of exercises for the page and total count.
        """
        total = self.session.execute(
            select(func.count()).select_from(ExerciseTable).where(
                ExerciseTable.user_id == user_id
            )
        ).scalar() or 0

        column = getattr(ExerciseTable, sort_by)
        order = column.desc() if sort_order == "desc" else column.asc()
        statement = (
            select(ExerciseTable)
            .where(ExerciseTable.user_id == user_id)
            .order_by(order)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        results = self.session.exec(statement).all()
        items = [ExerciseResponse.model_validate(ex.model_dump()) for ex in results]
        return items, total

    def get_by_id(self, exercise_id: int, user_id: int) -> ExerciseResponse | None:
        """Retrieve a specific exercise by ID, scoped to user.

        Args:
            exercise_id: The unique identifier of the exercise
            user_id: Owner's user ID

        Returns:
            The exercise if found and owned by user, None otherwise.
        """
        statement = select(ExerciseTable).where(
            ExerciseTable.id == exercise_id,
            ExerciseTable.user_id == user_id,
        )
        exercise = self.session.exec(statement).first()
        if exercise:
            return ExerciseResponse.model_validate(exercise.model_dump())
        return None

    def create(
        self,
        user_id: int,
        name: str,
        sets: int,
        reps: int,
        weight: float | None = None,
        workout_day: str = 'A'
    ) -> ExerciseResponse:
        """Create a new exercise for a user.

        Args:
            user_id: Owner's user ID
            name: Exercise name
            sets: Number of sets
            reps: Number of repetitions
            weight: Weight in kg (optional)
            workout_day: Workout day identifier (A-G or 'None')

        Returns:
            The newly created exercise with ID.
        """
        exercise = ExerciseTable(
            name=name,
            sets=sets,
            reps=reps,
            weight=weight,
            workout_day=workout_day,
            user_id=user_id,
        )
        self.session.add(exercise)
        self.session.commit()
        self.session.refresh(exercise)
        return ExerciseResponse.model_validate(exercise.model_dump())

    def update(
        self,
        exercise_id: int,
        user_id: int,
        name: str | None = None,
        sets: int | None = None,
        reps: int | None = None,
        weight: float | None = None,
        update_weight: bool = False,
        workout_day: str | None = None
    ) -> ExerciseResponse | None:
        """Update an existing exercise owned by a user.

        Args:
            exercise_id: ID of exercise to update
            user_id: Owner's user ID
            name: New name (optional)
            sets: New sets count (optional)
            reps: New reps count (optional)
            weight: New weight (optional)
            update_weight: If True, update weight even if None
            workout_day: New workout day (optional)

        Returns:
            The updated exercise if found, None otherwise.
        """
        statement = select(ExerciseTable).where(
            ExerciseTable.id == exercise_id,
            ExerciseTable.user_id == user_id,
        )
        exercise = self.session.exec(statement).first()
        if not exercise:
            return None

        if name is not None:
            exercise.name = name
        if sets is not None:
            exercise.sets = sets
        if reps is not None:
            exercise.reps = reps
        if weight is not None or update_weight:
            exercise.weight = weight
        if workout_day is not None:
            exercise.workout_day = workout_day

        self.session.add(exercise)
        self.session.commit()
        self.session.refresh(exercise)
        return ExerciseResponse.model_validate(exercise.model_dump())

    def delete(self, exercise_id: int, user_id: int) -> bool:
        """Delete an exercise owned by a user.

        Args:
            exercise_id: ID of exercise to delete
            user_id: Owner's user ID

        Returns:
            True if deleted, False if not found
        """
        statement = select(ExerciseTable).where(
            ExerciseTable.id == exercise_id,
            ExerciseTable.user_id == user_id,
        )
        exercise = self.session.exec(statement).first()
        if not exercise:
            return False

        self.session.delete(exercise)
        self.session.commit()
        return True

    def delete_all(self, user_id: int) -> int:
        """Delete all exercises owned by a user.

        Args:
            user_id: Owner's user ID

        Returns:
            Number of exercises deleted
        """
        statement = select(ExerciseTable).where(ExerciseTable.user_id == user_id)
        exercises = self.session.exec(statement).all()
        count = len(exercises)
        for exercise in exercises:
            self.session.delete(exercise)
        self.session.commit()
        return count

    def seed_initial_data(self, user_id: int, split: str = 'ppl') -> int:
        """Seed database with initial workout data for a specific user.

        Only seeds if the user has no exercises yet.

        Args:
            user_id: User to seed data for
            split: Workout split type — 'ppl', 'ab', or 'fullbody'

        Returns:
            Number of exercises seeded (0 if user already has exercises)
        """
        # Check if user already has exercises
        statement = select(ExerciseTable).where(ExerciseTable.user_id == user_id)
        existing = self.session.exec(statement).first()
        if existing:
            return 0

        daily = [
            ExerciseTable(name='Crunches', sets=1, reps=30, weight=None, workout_day='None', user_id=user_id),
            ExerciseTable(name='Penguins', sets=1, reps=25, weight=None, workout_day='None', user_id=user_id),
            ExerciseTable(name='Leg drops', sets=1, reps=25, weight=None, workout_day='None', user_id=user_id),
            ExerciseTable(name='Plank', sets=1, reps=90, weight=None, workout_day='None', user_id=user_id),
            ExerciseTable(name='Running', sets=1, reps=30, weight=None, workout_day='None', user_id=user_id),
        ]

        if split == 'fullbody':
            split_exercises = [
                ExerciseTable(name='Squats', sets=3, reps=8, weight=80.0, workout_day='A', user_id=user_id),
                ExerciseTable(name='Bench Press', sets=3, reps=8, weight=80.0, workout_day='A', user_id=user_id),
                ExerciseTable(name='Bent Over Row', sets=3, reps=8, weight=70.0, workout_day='A', user_id=user_id),
                ExerciseTable(name='Overhead Press', sets=3, reps=8, weight=50.0, workout_day='A', user_id=user_id),
                ExerciseTable(name='Romanian Deadlift', sets=3, reps=10, weight=80.0, workout_day='A', user_id=user_id),
                ExerciseTable(name='Pull ups', sets=3, reps=8, weight=None, workout_day='A', user_id=user_id),
                ExerciseTable(name='Bicep Curl', sets=3, reps=12, weight=20.0, workout_day='A', user_id=user_id),
                ExerciseTable(name='Tricep Pushdown', sets=3, reps=12, weight=25.0, workout_day='A', user_id=user_id),
            ]
        elif split == 'ab':
            split_exercises = [
                # Day A — Upper
                ExerciseTable(name='Bench Press', sets=3, reps=8, weight=80.0, workout_day='A', user_id=user_id),
                ExerciseTable(name='Incline Dumbbell Press', sets=3, reps=10, weight=25.0, workout_day='A', user_id=user_id),
                ExerciseTable(name='Cable Row', sets=3, reps=10, weight=70.0, workout_day='A', user_id=user_id),
                ExerciseTable(name='Pull ups', sets=3, reps=8, weight=None, workout_day='A', user_id=user_id),
                ExerciseTable(name='Shoulder Press', sets=3, reps=10, weight=40.0, workout_day='A', user_id=user_id),
                ExerciseTable(name='Bicep Curl', sets=3, reps=12, weight=20.0, workout_day='A', user_id=user_id),
                ExerciseTable(name='Tricep Extension', sets=3, reps=12, weight=25.0, workout_day='A', user_id=user_id),
                # Day B — Lower
                ExerciseTable(name='Squats', sets=4, reps=6, weight=100.0, workout_day='B', user_id=user_id),
                ExerciseTable(name='Romanian Deadlift', sets=3, reps=8, weight=90.0, workout_day='B', user_id=user_id),
                ExerciseTable(name='Leg Press', sets=3, reps=12, weight=150.0, workout_day='B', user_id=user_id),
                ExerciseTable(name='Hip Thrust', sets=3, reps=10, weight=90.0, workout_day='B', user_id=user_id),
                ExerciseTable(name='Leg Curl', sets=3, reps=12, weight=70.0, workout_day='B', user_id=user_id),
                ExerciseTable(name='Calf Raises', sets=4, reps=15, weight=60.0, workout_day='B', user_id=user_id),
            ]
        else:  # ppl
            split_exercises = [
                # Day A — Push
                ExerciseTable(name='Bench Press', sets=3, reps=10, weight=100.0, workout_day='A', user_id=user_id),
                ExerciseTable(name='Shoulder Press', sets=3, reps=10, weight=22.5, workout_day='A', user_id=user_id),
                ExerciseTable(name='Tricep Extension', sets=3, reps=10, weight=42.5, workout_day='A', user_id=user_id),
                ExerciseTable(name='Incline Bench Press', sets=3, reps=10, weight=37.5, workout_day='A', user_id=user_id),
                ExerciseTable(name='Chest Fly', sets=3, reps=10, weight=20.0, workout_day='A', user_id=user_id),
                ExerciseTable(name='Upper Chest Fly', sets=3, reps=10, weight=20.0, workout_day='A', user_id=user_id),
                ExerciseTable(name='Shoulder Extension', sets=5, reps=8, weight=12.5, workout_day='A', user_id=user_id),
                ExerciseTable(name='Overhead Tricep Extension', sets=3, reps=8, weight=17.5, workout_day='A', user_id=user_id),
                # Day B — Pull
                ExerciseTable(name='Pull ups', sets=5, reps=8, weight=None, workout_day='B', user_id=user_id),
                ExerciseTable(name='Cable Row', sets=3, reps=12, weight=80.0, workout_day='B', user_id=user_id),
                ExerciseTable(name='Pull Over', sets=3, reps=10, weight=45.0, workout_day='B', user_id=user_id),
                ExerciseTable(name='Dumbbell Shrugs', sets=3, reps=12, weight=35.0, workout_day='B', user_id=user_id),
                ExerciseTable(name='Rear Delt', sets=3, reps=10, weight=10.0, workout_day='B', user_id=user_id),
                ExerciseTable(name='Bicep Curl', sets=3, reps=10, weight=35.0, workout_day='B', user_id=user_id),
                ExerciseTable(name='Bicep Hammer Curls', sets=3, reps=8, weight=25.0, workout_day='B', user_id=user_id),
                # Day C — Legs
                ExerciseTable(name='Squats', sets=3, reps=8, weight=95.0, workout_day='C', user_id=user_id),
                ExerciseTable(name='Hip Thrust', sets=3, reps=10, weight=100.0, workout_day='C', user_id=user_id),
                ExerciseTable(name='Bulgarian Split Squat', sets=3, reps=8, weight=27.5, workout_day='C', user_id=user_id),
                ExerciseTable(name='Hip Adduction', sets=3, reps=16, weight=90.0, workout_day='C', user_id=user_id),
                ExerciseTable(name='Hip Abduction', sets=3, reps=16, weight=90.0, workout_day='C', user_id=user_id),
                ExerciseTable(name='Knee Extension', sets=3, reps=10, weight=164.0, workout_day='C', user_id=user_id),
                ExerciseTable(name='Knee Flexion', sets=3, reps=10, weight=90.0, workout_day='C', user_id=user_id),
            ]

        seed_exercises = split_exercises + daily

        for exercise in seed_exercises:
            self.session.add(exercise)

        self.session.commit()
        return len(seed_exercises)
