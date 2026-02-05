"""SQLModel-based repository for Workout Tracker API.

Provides CRUD operations for exercises using SQLModel ORM.
This replaces the raw SQL implementation with proper ORM patterns.
"""
from typing import List, Optional
from sqlmodel import Session, select
from sqlalchemy import func

from services.api.src.database.db_models import ExerciseTable
from services.api.src.database.models import ExerciseResponse


class ExerciseRepository:
    """Repository for exercise CRUD operations using SQLModel.

    This class encapsulates all database operations for exercises,
    providing a clean interface for the API layer.

    Attributes:
        session: SQLModel database session
    """

    def __init__(self, session: Session):
        """Initialize repository with a database session.

        Args:
            session: SQLModel session for database operations
        """
        self.session = session

    def get_all(self) -> List[ExerciseResponse]:
        """Retrieve all exercises from the database.

        Returns:
            List[ExerciseResponse]: List of all exercises
        """
        statement = select(ExerciseTable)
        results = self.session.exec(statement).all()
        return [ExerciseResponse.model_validate(ex.model_dump()) for ex in results]

    def list_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "id",
        sort_order: str = "asc",
    ) -> tuple[list[ExerciseResponse], int]:
        """Retrieve paginated and sorted exercises.

        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            sort_by: Column name to sort by
            sort_order: 'asc' or 'desc'

        Returns:
            Tuple of (exercises for the page, total count)
        """
        total = self.session.execute(
            select(func.count()).select_from(ExerciseTable)
        ).scalar() or 0

        column = getattr(ExerciseTable, sort_by)
        order = column.desc() if sort_order == "desc" else column.asc()
        statement = (
            select(ExerciseTable)
            .order_by(order)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        results = self.session.exec(statement).all()
        items = [ExerciseResponse.model_validate(ex.model_dump()) for ex in results]
        return items, total

    def get_by_id(self, exercise_id: int) -> Optional[ExerciseResponse]:
        """Retrieve a specific exercise by ID.

        Args:
            exercise_id: The unique identifier of the exercise

        Returns:
            ExerciseResponse if found, None otherwise
        """
        exercise = self.session.get(ExerciseTable, exercise_id)
        if exercise:
            return ExerciseResponse.model_validate(exercise.model_dump())
        return None

    def create(
        self,
        name: str,
        sets: int,
        reps: int,
        weight: Optional[float] = None,
        workout_day: str = 'A'
    ) -> ExerciseResponse:
        """Create a new exercise in the database.

        Args:
            name: Exercise name
            sets: Number of sets
            reps: Number of repetitions
            weight: Weight in kg (optional)
            workout_day: Workout day identifier (A-G or 'None')

        Returns:
            ExerciseResponse: The newly created exercise with ID
        """
        exercise = ExerciseTable(
            name=name,
            sets=sets,
            reps=reps,
            weight=weight,
            workout_day=workout_day
        )
        self.session.add(exercise)
        self.session.commit()
        self.session.refresh(exercise)
        return ExerciseResponse.model_validate(exercise.model_dump())

    def update(
        self,
        exercise_id: int,
        name: Optional[str] = None,
        sets: Optional[int] = None,
        reps: Optional[int] = None,
        weight: Optional[float] = None,
        update_weight: bool = False,
        workout_day: Optional[str] = None
    ) -> Optional[ExerciseResponse]:
        """Update an existing exercise.

        Args:
            exercise_id: ID of exercise to update
            name: New name (optional)
            sets: New sets count (optional)
            reps: New reps count (optional)
            weight: New weight (optional)
            update_weight: If True, update weight even if None
            workout_day: New workout day (optional)

        Returns:
            ExerciseResponse if found and updated, None otherwise
        """
        exercise = self.session.get(ExerciseTable, exercise_id)
        if not exercise:
            return None

        # Update only provided fields
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

    def delete(self, exercise_id: int) -> bool:
        """Delete an exercise by ID.

        Args:
            exercise_id: ID of exercise to delete

        Returns:
            True if deleted, False if not found
        """
        exercise = self.session.get(ExerciseTable, exercise_id)
        if not exercise:
            return False

        self.session.delete(exercise)
        self.session.commit()
        return True

    def seed_initial_data(self) -> int:
        """Seed database with initial workout data if empty.

        Returns:
            Number of exercises seeded
        """
        # Check if database is empty
        statement = select(ExerciseTable)
        existing = self.session.exec(statement).first()
        if existing:
            return 0

        # Seed data
        seed_exercises = [
            ExerciseTable(name='Bench Press', sets=3, reps=10, weight=95, workout_day='A'),
            ExerciseTable(name='Shoulder Press', sets=3, reps=10, weight=22.5, workout_day='A'),
            ExerciseTable(name='Tricep curl', sets=3, reps=10, weight=42.5, workout_day='A'),
            ExerciseTable(name='Pull ups', sets=3, reps=8, weight=None, workout_day='B'),
            ExerciseTable(name='Push ups', sets=3, reps=15, weight=None, workout_day='A'),
            ExerciseTable(name='Squats', sets=3, reps=8, weight=60, workout_day='C'),
            ExerciseTable(name='Hip Thrust', sets=3, reps=8, weight=45, workout_day='C'),
            ExerciseTable(name='Plank', sets=3, reps=60, weight=None, workout_day='B'),
        ]

        for exercise in seed_exercises:
            self.session.add(exercise)

        self.session.commit()
        return len(seed_exercises)