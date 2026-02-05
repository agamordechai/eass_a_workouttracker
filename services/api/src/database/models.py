"""Pydantic models (schemas) for the Workout Tracker API."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class Exercise(BaseModel):
    """Exercise model for creating new exercises.

    Attributes:
        name (str): The name of the exercise (1-100 characters).
        sets (int): The number of sets to perform (1-100).
        reps (int): The number of repetitions per set (1-1000).
        weight (Optional[float]): The weight used in kg (optional, >= 0).
        workout_day (str): The workout day identifier (e.g., A, B, C for splits).
    """
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Name of the exercise",
        examples=["Bench Press", "Squat", "Pull-ups"]
    )
    sets: int = Field(
        ...,
        ge=1,
        le=100,
        description="Number of sets to perform",
        examples=[3, 4, 5]
    )
    reps: int = Field(
        ...,
        ge=1,
        le=1000,
        description="Number of repetitions per set",
        examples=[8, 10, 12]
    )
    weight: Optional[float] = Field(
        default=None,
        ge=0,
        description="Weight in kg (None for bodyweight exercises)",
        examples=[60.0, 80.5, None]
    )
    workout_day: str = Field(
        default='A',
        min_length=1,
        max_length=10,
        description="Workout day identifier (A-G for specific days, 'None' for daily exercises)",
        examples=["A", "B", "C", "None"]
    )


class ExerciseResponse(BaseModel):
    """Exercise response model for returning exercise data.

    Attributes:
        id (int): The unique identifier of the exercise.
        name (str): The name of the exercise (1-100 characters).
        sets (int): The number of sets to perform (1-100).
        reps (int): The number of repetitions per set (1-1000).
        weight (Optional[float]): The weight used in kg (optional, >= 0).
        workout_day (str): The workout day identifier (e.g., A, B, C for splits).
    """
    id: int = Field(..., ge=1, description="Unique identifier of the exercise")
    name: str = Field(..., min_length=1, max_length=100, description="Name of the exercise")
    sets: int = Field(..., ge=1, le=100, description="Number of sets")
    reps: int = Field(..., ge=1, le=1000, description="Number of reps per set")
    weight: Optional[float] = Field(default=None, ge=0, description="Weight in kg")
    workout_day: str = Field(..., min_length=1, max_length=10, description="Workout day identifier (A-G for specific days, 'None' for daily exercises)")


class PaginatedExerciseResponse(BaseModel):
    """Paginated response wrapping a list of exercises."""
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, description="Items per page")
    total: int = Field(..., ge=0, description="Total number of exercises across all pages")
    items: list[ExerciseResponse] = Field(..., description="Exercises on this page")


class ExerciseEditRequest(BaseModel):
    """Exercise edit request model for updating exercises.

    All attributes are optional to allow partial updates of exercise data.

    Attributes:
        name (Optional[str]): The new name for the exercise (1-100 characters).
        sets (Optional[int]): The new number of sets (1-100).
        reps (Optional[int]): The new number of repetitions (1-1000).
        weight (Optional[float]): The new weight value in kg (>= 0, or None for bodyweight).
        workout_day (Optional[str]): The workout day identifier (A, B, C, etc.).
    """
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="New name for the exercise"
    )
    sets: Optional[int] = Field(
        default=None,
        ge=1,
        le=100,
        description="New number of sets"
    )
    reps: Optional[int] = Field(
        default=None,
        ge=1,
        le=1000,
        description="New number of reps"
    )
    weight: Optional[float] = Field(
        default=None,
        ge=0,
        description="New weight in kg (None for bodyweight)"
    )
    workout_day: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=10,
        description="New workout day identifier (A-G for specific days, 'None' for daily exercises)"
    )


class HealthResponse(BaseModel):
    """Health check response model.

    Attributes:
        status (str): Overall health status ('healthy' or 'unhealthy').
        version (str): API version string.
        timestamp (str): ISO 8601 timestamp of the health check.
        database (Dict[str, Any]): Database connectivity information.
    """
    status: str = Field(..., description="Health status: 'healthy' or 'unhealthy'")
    version: str = Field(..., description="API version")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    database: Dict[str, Any] = Field(..., description="Database status info")
