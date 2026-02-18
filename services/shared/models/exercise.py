"""Unified Exercise models for all services.

These models are used across API, AI Coach, and Worker services to ensure
consistent data representation and validation.
"""

from pydantic import BaseModel, Field


class ExerciseBase(BaseModel):
    """Base exercise model with common fields.

    Attributes:
        name: The name of the exercise (1-100 characters).
        sets: The number of sets to perform (1-100).
        reps: The number of repetitions per set (1-1000).
        weight: The weight used in kg (optional, >= 0).
        workout_day: The workout day identifier (e.g., A, B, C for splits).
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Name of the exercise",
        examples=["Bench Press", "Squat", "Pull-ups"],
    )
    sets: int = Field(..., ge=1, le=100, description="Number of sets to perform", examples=[3, 4, 5])
    reps: int = Field(..., ge=1, le=1000, description="Number of repetitions per set", examples=[8, 10, 12])
    weight: float | None = Field(
        default=None, ge=0, description="Weight in kg (None for bodyweight exercises)", examples=[60.0, 80.5, None]
    )
    workout_day: str = Field(
        default="A",
        min_length=1,
        max_length=10,
        description="Workout day identifier (A-G for specific days, 'None' for daily exercises)",
        examples=["A", "B", "C", "None"],
    )


class ExerciseCreate(ExerciseBase):
    """Exercise model for creating new exercises.

    Inherits all fields from ExerciseBase without modifications.
    """

    pass


class ExerciseResponse(ExerciseBase):
    """Exercise response model for returning exercise data.

    Extends ExerciseBase with database-specific fields like ID and timestamps.

    Attributes:
        id: The unique identifier of the exercise.
    """

    id: int = Field(..., ge=1, description="Unique identifier of the exercise")

    model_config = {"from_attributes": True}


class ExerciseEditRequest(BaseModel):
    """Exercise edit request model for updating exercises.

    All attributes are optional to allow partial updates of exercise data.

    Attributes:
        name: The new name for the exercise (1-100 characters).
        sets: The new number of sets (1-100).
        reps: The new number of repetitions (1-1000).
        weight: The new weight value in kg (>= 0, or None for bodyweight).
        workout_day: The workout day identifier (A, B, C, etc.).
    """

    name: str | None = Field(default=None, min_length=1, max_length=100, description="New name for the exercise")
    sets: int | None = Field(default=None, ge=1, le=100, description="New number of sets")
    reps: int | None = Field(default=None, ge=1, le=1000, description="New number of reps")
    weight: float | None = Field(default=None, ge=0, description="New weight in kg (None for bodyweight)")
    workout_day: str | None = Field(
        default=None,
        min_length=1,
        max_length=10,
        description="New workout day identifier (A-G for specific days, 'None' for daily exercises)",
    )


class PaginatedExerciseResponse(BaseModel):
    """Paginated response wrapping a list of exercises."""

    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, description="Items per page")
    total: int = Field(..., ge=0, description="Total number of exercises across all pages")
    items: list[ExerciseResponse] = Field(..., description="Exercises on this page")
