"""Pydantic models for the AI Coach service."""
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


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


class ExerciseFromAPI(BaseModel):
    """Exercise model matching the main API response."""
    id: int
    name: str
    sets: int
    reps: int
    weight: Optional[float] = None
    workout_day: str = "A"  # A-G for specific days, "None" for daily exercises


class WorkoutContext(BaseModel):
    """Context for AI recommendations based on current workout data."""
    exercises: List[ExerciseFromAPI] = Field(default_factory=list)
    total_volume: float = Field(default=0.0, description="Total workout volume in kg")
    exercise_count: int = Field(default=0, description="Total number of exercises")
    muscle_groups_worked: List[str] = Field(default_factory=list)


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
    focus_area: Optional[MuscleGroup] = Field(default=None, description="Target muscle group")
    equipment_available: List[str] = Field(
        default_factory=lambda: ["barbell", "dumbbells", "cables", "bodyweight"],
        description="Available equipment"
    )
    session_duration_minutes: int = Field(default=60, ge=15, le=180, description="Workout duration")


class ExerciseRecommendation(BaseModel):
    """A single exercise recommendation."""
    name: str = Field(..., description="Exercise name")
    sets: int = Field(..., ge=1, le=10, description="Recommended sets")
    reps: str = Field(..., description="Recommended reps (can be range like '8-12')")
    weight_suggestion: Optional[str] = Field(default=None, description="Weight suggestion")
    notes: Optional[str] = Field(default=None, description="Form tips or notes")
    muscle_group: MuscleGroup = Field(..., description="Primary muscle group")


class WorkoutRecommendation(BaseModel):
    """Full workout recommendation."""
    title: str = Field(..., description="Workout title")
    description: str = Field(..., description="Workout description")
    exercises: List[ExerciseRecommendation] = Field(..., description="Recommended exercises")
    estimated_duration_minutes: int = Field(..., description="Estimated duration")
    difficulty: str = Field(..., description="Workout difficulty level")
    tips: List[str] = Field(default_factory=list, description="General workout tips")


class ProgressAnalysis(BaseModel):
    """Analysis of workout progress."""
    summary: str = Field(..., description="Progress summary")
    strengths: List[str] = Field(default_factory=list, description="Training strengths")
    areas_to_improve: List[str] = Field(default_factory=list, description="Areas needing attention")
    recommendations: List[str] = Field(default_factory=list, description="Actionable recommendations")
    muscle_balance_score: Optional[float] = Field(default=None, ge=0, le=100, description="Balance score")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    service: str = Field(default="ai-coach", description="Service name")
    ai_model: str = Field(..., description="AI model being used")
    workout_api_connected: bool = Field(..., description="Workout API connection status")
    redis_connected: bool = Field(..., description="Redis connection status")

