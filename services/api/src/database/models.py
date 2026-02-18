"""Pydantic models (schemas) for the Workout Tracker API.

This module imports shared exercise models and defines API-specific models.
The shared models ensure consistency across all microservices.
"""

from typing import Any

from pydantic import BaseModel, Field

# Import shared exercise models (single source of truth)
from services.shared.models import (
    ExerciseBase as Exercise,
)
from services.shared.models import (
    ExerciseEditRequest,
    ExerciseResponse,
    PaginatedExerciseResponse,
)

# Re-export for backward compatibility
__all__ = [
    "Exercise",
    "ExerciseResponse",
    "ExerciseEditRequest",
    "PaginatedExerciseResponse",
    "HealthResponse",
]


class HealthResponse(BaseModel):
    """Health check response model.

    Attributes:
        status: Overall health status ('healthy' or 'unhealthy').
        version: API version string.
        timestamp: ISO 8601 timestamp of the health check.
        database: Database connectivity information.
    """

    status: str = Field(..., description="Health status: 'healthy' or 'unhealthy'")
    version: str = Field(..., description="API version")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    database: dict[str, Any] = Field(..., description="Database status info")
