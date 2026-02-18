"""Cleanup task - remove stale idempotency keys and old data."""

import logging
from typing import Any

try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

from ..config import get_settings

logger = logging.getLogger(__name__)


async def cleanup_stale_data(ctx: dict[str, Any]) -> dict[str, int]:
    """Arq task to clean up stale data from Redis.

    Removes expired idempotency keys and other stale data to keep Redis clean.
    Note: Redis automatically removes keys with expired TTL, but this task
    explicitly scans and cleans up to ensure consistency.

    Args:
        ctx: Arq context dictionary

    Returns:
        Summary dict with cleanup statistics
    """
    settings = get_settings()
    logger.info("Starting weekly cleanup job")

    if not REDIS_AVAILABLE:
        logger.warning("Redis not available, skipping cleanup")
        return {"deleted_idempotency_keys": 0, "cleanup_time_ms": 0}

    # Connect to cache Redis (DB 0)
    redis_client = redis.from_url(settings.redis_cache_url, decode_responses=True)

    try:
        await redis_client.ping()
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        await redis_client.aclose()
        return {"deleted_idempotency_keys": 0, "cleanup_time_ms": 0}

    import time

    start_time = time.time()

    deleted_count = 0

    try:
        # Scan for idempotency keys
        cursor = 0
        while True:
            cursor, keys = await redis_client.scan(cursor=cursor, match="idempotency:*", count=100)

            for key in keys:
                # Check if key has TTL (>0 means it will expire, -1 means no expiry, -2 means doesn't exist)
                ttl = await redis_client.ttl(key)

                # Delete keys without TTL or with very short TTL (< 60 seconds)
                # This shouldn't happen normally but cleans up orphaned keys
                if ttl == -1 or (ttl > 0 and ttl < 60):
                    await redis_client.delete(key)
                    deleted_count += 1
                    logger.debug(f"Deleted stale idempotency key: {key} (TTL: {ttl})")

            if cursor == 0:
                break

        cleanup_time_ms = int((time.time() - start_time) * 1000)

        logger.info(f"Cleanup complete: deleted {deleted_count} keys in {cleanup_time_ms}ms")

        return {
            "deleted_idempotency_keys": deleted_count,
            "cleanup_time_ms": cleanup_time_ms,
        }

    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        return {
            "deleted_idempotency_keys": deleted_count,
            "cleanup_time_ms": int((time.time() - start_time) * 1000),
        }

    finally:
        await redis_client.aclose()
