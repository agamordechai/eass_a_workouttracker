"""AI cache warmup task - pre-generate common AI recommendations."""

import asyncio
import logging
from typing import Any

from ..clients import get_ai_coach_client

logger = logging.getLogger(__name__)


async def warmup_ai_cache(ctx: dict[str, Any]) -> dict[str, int]:
    """Arq task to warm up AI Coach cache with common queries.

    Pre-generates AI recommendations for popular muscle groups, equipment combos,
    and workout durations to improve response times for users.

    Args:
        ctx: Arq context dictionary

    Returns:
        Summary dict with total_requests, successful, failed counts
    """
    logger.info("Starting daily AI cache warmup job")

    client = get_ai_coach_client()

    # Common muscle groups
    muscle_groups = ["chest", "back", "shoulders", "legs", "biceps", "triceps", "core"]

    # Common equipment combinations
    equipment_combos = [
        ["barbell", "dumbbells"],
        ["barbell", "dumbbells", "cables"],
        ["bodyweight"],
        ["dumbbells"],
        ["cables", "dumbbells"],
    ]

    # Common durations (minutes)
    durations = [30, 45, 60, 90]

    total_requests = 0
    successful = 0
    failed = 0

    # Generate all combinations
    for muscle in muscle_groups:
        for equipment in equipment_combos:
            for duration in durations:
                try:
                    # Make request to AI Coach /recommend endpoint
                    response = await client.post(
                        "/recommend",
                        json={
                            "focus_area": muscle,
                            "equipment_available": equipment,
                            "session_duration_minutes": duration,
                        },
                    )
                    response.raise_for_status()

                    total_requests += 1
                    successful += 1

                    logger.debug(f"Warmed cache: muscle={muscle}, equipment={equipment}, duration={duration}min")

                    # Rate limiting - 0.5s between requests
                    await asyncio.sleep(0.5)

                except Exception as e:
                    total_requests += 1
                    failed += 1
                    logger.warning(
                        f"Failed to warm cache for muscle={muscle}, equipment={equipment}, duration={duration}min: {e}"
                    )

    logger.info(f"AI cache warmup complete: total={total_requests}, successful={successful}, failed={failed}")

    return {
        "total_requests": total_requests,
        "successful": successful,
        "failed": failed,
    }
