"""Exercise refresh task - migrated from scripts/refresh.py."""

import logging
from typing import Any

try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

from dev.refresh import ExerciseRefresher, RefreshConfig

from ..config import get_settings

logger = logging.getLogger(__name__)


async def refresh_exercises(ctx: dict[str, Any]) -> dict[str, int]:
    """Arq task to refresh all exercises.

    This task migrates the logic from scripts/refresh.py to run as a scheduled job.
    It uses bounded concurrency, idempotency, and retry logic.

    Args:
        ctx: Arq context dictionary (contains redis pool, job_id, etc.)

    Returns:
        Summary dict with processed, skipped, failed counts
    """
    settings = get_settings()
    logger.info("Starting hourly exercise refresh job")

    # Create refresh config from worker settings
    config = RefreshConfig(
        api_url=settings.api_client__workout_api_url,
        redis_url=settings.redis_cache_url,  # Use cache DB for idempotency
        max_concurrency=settings.refresh__concurrency,
        max_retries=settings.refresh__max_retries,
        retry_base_delay=settings.refresh__retry_delay,
        idempotency_ttl=settings.refresh__idempotency_ttl,
        timeout=settings.api_client__timeout,
    )

    # Run refresh
    async with ExerciseRefresher(config) as refresher:
        await refresher.refresh_all()
        summary = refresher.get_summary()

    logger.info(
        f"Exercise refresh complete: processed={summary['processed']}, "
        f"skipped={summary['skipped']}, failed={summary['failed']}, "
        f"success_rate={summary['success_rate']:.1f}%"
    )

    return {
        "processed": summary["processed"],
        "skipped": summary["skipped"],
        "failed": summary["failed"],
        "total": summary["total"],
        "success_rate": summary["success_rate"],
    }
