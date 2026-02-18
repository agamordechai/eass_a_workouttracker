"""Pydantic models for the AI Coach service."""

from enum import Enum

from pydantic import BaseModel, Field

# Import shared Exercise models
from services.shared.models import ExerciseResponse

# Alias for backward compatibility
ExerciseFromAPI = ExerciseResponse


class MuscleGroup(str, Enum):
    """Muscle groups for workout categorization."""

    CHEST = "chest"
    BACK = "back"
    SHOULDERS = "shoulders"
    BICEPS = "biceps"
    TRICEPS = "triceps"
    LEGS = "legs"
    CORE = "core"
    FULL_BODY = "full_body"
    UPPER_LOWER = "upper_lower"
    PUSH_PULL_LEGS = "push_pull_legs"


class WorkoutContext(BaseModel):
    """Context for AI recommendations based on current workout data."""

    exercises: list[ExerciseFromAPI] = Field(default_factory=list)
    total_volume: float = Field(default=0.0, description="Total workout volume in kg")
    exercise_count: int = Field(default=0, description="Total number of exercises")
    muscle_groups_worked: list[str] = Field(default_factory=list)


class ChatMessage(BaseModel):
    """A single chat message."""

    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Request for chat endpoint."""

    message: str = Field(..., min_length=1, max_length=2000, description="User message")
    include_workout_context: bool = Field(default=True, description="Include current workout data")


class ChatResponse(BaseModel):
    """Response from chat endpoint."""

    response: str = Field(..., description="AI coach response")
    context_used: bool = Field(..., description="Whether workout context was included")


class RecommendationRequest(BaseModel):
    """Request for workout recommendations."""

    focus_area: MuscleGroup | None = Field(default=None, description="Target muscle group")
    custom_focus_area: str | None = Field(
        default=None, max_length=200, description="Freeform focus area (overrides focus_area when set)"
    )
    equipment_available: list[str] = Field(
        default_factory=lambda: ["barbell", "dumbbells", "cables", "bodyweight"], description="Available equipment"
    )
    session_duration_minutes: int = Field(default=60, ge=15, le=180, description="Workout duration")


class ExerciseRecommendation(BaseModel):
    """A single exercise recommendation."""

    name: str = Field(..., description="Exercise name")
    sets: int = Field(..., ge=1, le=10, description="Recommended sets")
    reps: str = Field(..., description="Recommended reps (can be range like '8-12')")
    weight_suggestion: str | None = Field(default=None, description="Weight suggestion")
    notes: str | None = Field(default=None, description="Form tips or notes")
    muscle_group: MuscleGroup = Field(..., description="Primary muscle group")
    workout_day: str = Field(default="A", description="Workout day assignment (A, B, C, etc.)")


class WorkoutRecommendation(BaseModel):
    """Full workout recommendation."""

    title: str = Field(..., description="Workout title")
    description: str = Field(..., description="Workout description")
    exercises: list[ExerciseRecommendation] = Field(..., description="Recommended exercises")
    estimated_duration_minutes: int = Field(..., description="Estimated duration")
    difficulty: str = Field(..., description="Workout difficulty level")
    tips: list[str] = Field(default_factory=list, description="General workout tips")
    split_type: str = Field(
        default="Single Session", description="Split structure, e.g. 'Push/Pull/Legs', 'A/B Upper-Lower', 'Full Body'"
    )


class ProgressAnalysis(BaseModel):
    """Analysis of workout progress."""

    summary: str = Field(..., description="Progress summary")
    strengths: list[str] = Field(default_factory=list, description="Training strengths")
    areas_to_improve: list[str] = Field(default_factory=list, description="Areas needing attention")
    recommendations: list[str] = Field(default_factory=list, description="Actionable recommendations")
    muscle_balance_score: float | None = Field(default=None, ge=0, le=100, description="Balance score")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    service: str = Field(default="ai-coach", description="Service name")
    ai_model: str = Field(..., description="AI model being used")
    workout_api_connected: bool = Field(..., description="Workout API connection status")
    redis_connected: bool = Field(..., description="Redis connection status")
