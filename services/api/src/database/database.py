"""SQLModel database engine and session management.

This module provides database connection handling using SQLModel.
Supports both PostgreSQL and SQLite based on configuration.
"""
from typing import Generator
from sqlmodel import create_engine, Session, SQLModel
from services.api.src.database.config import get_settings


# Get settings
settings = get_settings()

# Create database URL
if settings.db.is_postgres:
    # PostgreSQL URL
    database_url = settings.db.url
    connect_args = {}
else:
    # SQLite URL
    database_url = f"sqlite:///{settings.db.path}"
    # SQLite-specific settings
    connect_args = {"check_same_thread": False}

# Create SQLModel engine
engine = create_engine(
    database_url,
    echo=settings.db.echo_sql,
    connect_args=connect_args,
)


def init_db() -> None:
    """Initialize database - placeholder for backward compatibility.

    NOTE: Database schema is now managed by Alembic migrations.
    To initialize or update the database schema, run:
        cd services/api && alembic upgrade head

    This function is kept for backward compatibility but no longer
    performs manual table creation.
    """
    # Import all models to ensure they're registered with SQLModel metadata
    from services.api.src.database.db_models import ExerciseTable  # noqa: F401

    # Manual table creation removed - use Alembic migrations instead
    # To create tables, run: alembic upgrade head
    pass


def get_session() -> Generator[Session, None, None]:
    """Provide a database session for dependency injection.

    Yields:
        Session: SQLModel session for database operations
    """
    with Session(engine) as session:
        yield session