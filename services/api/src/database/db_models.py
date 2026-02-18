"""SQLModel database table definitions for Workout Tracker.

This module defines the database tables using SQLModel ORM.
Separate from Pydantic models to maintain clear separation between
database layer and API layer.
"""

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class UserTable(SQLModel, table=True):
    """User database table model.

    Attributes:
        id: Auto-incrementing primary key
        google_id: Unique Google OAuth subject ID (None for email/password users)
        email: Unique user email
        name: User display name
        password_hash: Bcrypt hash of password (None for Google OAuth users)
        picture_url: User profile picture URL from Google
        role: User role (default 'user')
        disabled: Whether account is disabled
        created_at: Account creation timestamp
    """

    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    google_id: str | None = Field(default=None, unique=True, index=True, max_length=255)
    email: str = Field(unique=True, index=True, max_length=255)
    name: str = Field(max_length=255)
    password_hash: str | None = Field(default=None, max_length=255)
    picture_url: str | None = Field(default=None, max_length=1024)
    role: str = Field(default="user", max_length=20)
    disabled: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ExerciseTable(SQLModel, table=True):
    """Exercise database table model.

    This SQLModel class represents the 'exercises' table in the database.
    It uses SQLModel which combines SQLAlchemy ORM with Pydantic validation.

    Attributes:
        id: Auto-incrementing primary key
        name: Exercise name (required, max 100 chars)
        sets: Number of sets (required, 1-100)
        reps: Number of repetitions (required, 1-1000)
        weight: Weight in kg (optional for bodyweight exercises)
        workout_day: Workout day identifier (A-G or 'None')
        user_id: Foreign key to users table
    """

    __tablename__ = "exercises"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, index=True)
    sets: int = Field(ge=1, le=100)
    reps: int = Field(ge=1, le=1000)
    weight: float | None = Field(default=None, ge=0)
    workout_day: str = Field(default="A", max_length=10)
    user_id: int = Field(foreign_key="users.id", index=True)
