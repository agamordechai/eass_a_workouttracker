"""Arq worker entry point with cron job scheduling."""

import asyncio
import logging
from typing import Any

import uvicorn
from arq import cron
from arq.connections import RedisSettings
from arq.worker import create_worker

from .clients import close_clients
from .config import get_settings
from .tasks.cache_warmup import warmup_ai_cache
from .tasks.cleanup import cleanup_stale_data
from .tasks.refresh import refresh_exercises

# Configure logging
settings = get_settings()
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def startup(ctx: dict[str, Any]) -> None:
    """Worker startup hook.

    Args:
        ctx: Arq context dictionary
    """
    logger.info("=" * 60)
    logger.info("Worker Service Starting")
    logger.info("=" * 60)
    logger.info(f"Redis Queue URL: {settings.redis_queue_url}")
    logger.info(f"Redis Cache URL: {settings.redis_cache_url}")
    logger.info(f"API URL: {settings.api_client__workout_api_url}")
    logger.info(f"AI Coach URL: {settings.api_client__ai_coach_url}")
    logger.info(f"Max Jobs: {settings.worker__max_jobs}")
    logger.info(f"Job Timeout: {settings.worker__job_timeout}s")
    logger.info("=" * 60)

    # Count enabled cron jobs
    cron_jobs_count = sum(
        [
            settings.schedule__enable_hourly_refresh,
            settings.schedule__enable_daily_warmup,
            settings.schedule__enable_weekly_cleanup,
        ]
    )
    logger.info(f"Worker configured with 3 tasks and {cron_jobs_count} cron jobs")

    if settings.schedule__enable_hourly_refresh:
        logger.info("  - Hourly refresh: ENABLED (every hour on the hour)")
    if settings.schedule__enable_daily_warmup:
        logger.info(f"  - Daily warmup: ENABLED (daily at {settings.schedule__warmup_hour}:00 UTC)")
    if settings.schedule__enable_weekly_cleanup:
        logger.info(f"  - Weekly cleanup: ENABLED (Sunday at {settings.schedule__cleanup_hour}:00 UTC)")

    logger.info("=" * 60)


async def shutdown(ctx: dict[str, Any]) -> None:
    """Worker shutdown hook.

    Args:
        ctx: Arq context dictionary
    """
    logger.info("Worker shutting down...")
    await close_clients()
    logger.info("Worker shutdown complete")


class WorkerSettings:
    """Arq worker settings."""

    # Redis settings for job queue (DB 1)
    redis_settings = RedisSettings(
        host=settings.redis__host,
        port=settings.redis__port,
        database=settings.redis__database,
        password=settings.redis__password,
    )

    # Register task functions
    functions = [
        refresh_exercises,
        warmup_ai_cache,
        cleanup_stale_data,
    ]

    # Cron jobs - only include enabled ones
    cron_jobs = []

    if settings.schedule__enable_hourly_refresh:
        # Run every hour on the hour
        cron_jobs.append(cron(refresh_exercises, hour=None, minute=0, unique=True))

    if settings.schedule__enable_daily_warmup:
        # Run daily at configured hour (default 6 AM UTC)
        cron_jobs.append(cron(warmup_ai_cache, hour=settings.schedule__warmup_hour, minute=0, unique=True))

    if settings.schedule__enable_weekly_cleanup:
        # Run weekly on configured day at configured hour (default Sunday 2 AM UTC)
        cron_jobs.append(
            cron(
                cleanup_stale_data,
                weekday=settings.schedule__cleanup_day_of_week,
                hour=settings.schedule__cleanup_hour,
                minute=0,
                unique=True,
            )
        )

    # Worker settings
    max_jobs = settings.worker__max_jobs
    job_timeout = settings.worker__job_timeout

    # Lifecycle hooks
    on_startup = startup
    on_shutdown = shutdown


async def run_health_server():
    """Run the health check server concurrently with the worker."""
    from .health import app

    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=settings.worker__health_port,
        log_level=settings.log_level.lower(),
    )
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    """Main entry point - run worker and health server concurrently."""
    # Create worker
    worker = create_worker(WorkerSettings)

    # Run worker and health server concurrently
    await asyncio.gather(
        worker.async_run(),
        run_health_server(),
    )


if __name__ == "__main__":
    asyncio.run(main())
