"""FastAPI dependencies for database access.

Provides dependency injection for database sessions and repositories.
"""

from typing import Annotated

from fastapi import Depends
from sqlmodel import Session

from services.api.src.database.database import get_session
from services.api.src.database.sqlmodel_repository import ExerciseRepository
from services.api.src.database.user_repository import UserRepository


def get_exercise_repository(session: Annotated[Session, Depends(get_session)]) -> ExerciseRepository:
    """Provide an ExerciseRepository instance.

    Args:
        session: SQLModel session from dependency injection

    Returns:
        Repository instance for exercise operations
    """
    return ExerciseRepository(session)


def get_user_repository(session: Annotated[Session, Depends(get_session)]) -> UserRepository:
    """Provide a UserRepository instance.

    Args:
        session: SQLModel session from dependency injection

    Returns:
        Repository instance for user operations
    """
    return UserRepository(session)


# Type aliases for dependency injection
SessionDep = Annotated[Session, Depends(get_session)]
RepositoryDep = Annotated[ExerciseRepository, Depends(get_exercise_repository)]
UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]
