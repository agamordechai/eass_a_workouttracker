"""HTTP client for communicating with the Workout Tracker API."""

import httpx
import logging
from typing import List, Optional

from services.ai_coach.src.config import get_settings
from services.ai_coach.src.models import ExerciseFromAPI, WorkoutContext

logger = logging.getLogger(__name__)


class WorkoutAPIClient:
    """Client for the Workout Tracker API."""

    def __init__(self, base_url: Optional[str] = None, timeout: float = 10.0):
        """Initialize the API client.

        Args:
            base_url: Base URL of the Workout API
            timeout: Request timeout in seconds
        """
        settings = get_settings()
        self.base_url = base_url or settings.workout_api_url
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def health_check(self) -> bool:
        """Check if the Workout API is healthy.

        Returns:
            True if API is healthy, False otherwise
        """
        try:
            client = await self._get_client()
            response = await client.get("/health")
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Workout API health check failed: {e}")
            return False

    async def get_exercises(self) -> List[ExerciseFromAPI]:
        """Fetch all exercises from the Workout API.

        Returns:
            List of exercises
        """
        try:
            client = await self._get_client()
            # Fetch with large page_size to get all exercises (API max is 200)
            response = await client.get("/exercises?page_size=200")
            response.raise_for_status()
            data = response.json()

            # API returns paginated response: {'items': [...], 'page': 1, 'page_size': 20, 'total': N}
            if isinstance(data, dict) and 'items' in data:
                return [ExerciseFromAPI(**ex) for ex in data['items']]
            else:
                # Fallback for legacy non-paginated response
                return [ExerciseFromAPI(**ex) for ex in data]
        except Exception as e:
            logger.error(f"Failed to fetch exercises: {e}")
            return []

    async def get_workout_context(self) -> WorkoutContext:
        """Build workout context from current exercises.

        Returns:
            WorkoutContext with current workout data
        """
        exercises = await self.get_exercises()

        # Calculate total volume
        total_volume = sum(
            ex.sets * ex.reps * (ex.weight or 0)
            for ex in exercises
        )

        # Identify muscle groups (basic heuristic based on exercise names)
        muscle_groups = self._identify_muscle_groups(exercises)

        return WorkoutContext(
            exercises=exercises,
            total_volume=total_volume,
            exercise_count=len(exercises),
            muscle_groups_worked=muscle_groups
        )

    def _identify_muscle_groups(self, exercises: List[ExerciseFromAPI]) -> List[str]:
        """Identify muscle groups from exercise names.

        Args:
            exercises: List of exercises

        Returns:
            List of identified muscle groups
        """
        muscle_keywords = {
            "chest": ["bench", "chest", "fly", "push-up", "pushup", "pec"],
            "back": ["row", "pull", "lat", "deadlift", "back"],
            "shoulders": ["shoulder", "press", "lateral", "delt", "overhead"],
            "biceps": ["curl", "bicep"],
            "triceps": ["tricep", "extension", "dip", "pushdown"],
            "legs": ["squat", "leg", "lunge", "calf", "hamstring", "quad"],
            "core": ["ab", "plank", "crunch", "core", "sit-up"]
        }

        found_groups = set()
        for exercise in exercises:
            name_lower = exercise.name.lower()
            for group, keywords in muscle_keywords.items():
                if any(kw in name_lower for kw in keywords):
                    found_groups.add(group)

        return list(found_groups)


# Global client instance
_workout_client: Optional[WorkoutAPIClient] = None


def get_workout_client() -> WorkoutAPIClient:
    """Get the global workout API client."""
    global _workout_client
    if _workout_client is None:
        _workout_client = WorkoutAPIClient()
    return _workout_client


async def close_workout_client() -> None:
    """Close the global workout API client."""
    global _workout_client
    if _workout_client:
        await _workout_client.close()
        _workout_client = None

