"""Database module for Workout Tracker API - SQLModel version."""

from services.api.src.database.database import engine, get_session, init_db
from services.api.src.database.db_models import ExerciseTable
from services.api.src.database.dependencies import RepositoryDep, SessionDep
from services.api.src.database.models import Exercise, ExerciseEditRequest, ExerciseResponse
from services.api.src.database.sqlmodel_repository import ExerciseRepository

__all__ = [
    # SQLModel components
    "init_db",
    "get_session",
    "engine",
    "ExerciseTable",
    "ExerciseRepository",
    "RepositoryDep",
    "SessionDep",
    # Pydantic models
    "Exercise",
    "ExerciseResponse",
    "ExerciseEditRequest",
]
