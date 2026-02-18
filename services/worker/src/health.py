"""Health check server for worker service."""

import logging
from typing import Literal

try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

from fastapi import FastAPI
from pydantic import BaseModel

from .clients import get_ai_coach_client, get_api_client
from .config import get_settings

logger = logging.getLogger(__name__)

app = FastAPI(title="Worker Health Check")


class HealthResponse(BaseModel):
    """Health check response model."""

    status: Literal["healthy", "degraded", "unhealthy"]
    redis_connected: bool
    queue_depth: int | None = None
    api_connected: bool
    ai_coach_connected: bool
    details: dict[str, str] | None = None


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Comprehensive health check for worker service.

    Checks:
    - Redis connectivity (queue DB)
    - Queue depth
    - API connectivity
    - AI Coach connectivity

    Returns:
        HealthResponse with overall status and individual checks
    """
    settings = get_settings()
    details = {}

    # Check Redis connectivity
    redis_connected = False
    queue_depth = None

    if REDIS_AVAILABLE:
        try:
            redis_client = redis.from_url(settings.redis_queue_url, decode_responses=True)
            await redis_client.ping()
            redis_connected = True

            # Check queue depth
            queue_depth = await redis_client.llen("arq:queue")
            details["queue_depth"] = str(queue_depth)

            await redis_client.aclose()
        except Exception as e:
            details["redis_error"] = str(e)
            logger.warning(f"Redis health check failed: {e}")
    else:
        details["redis_error"] = "Redis package not installed"

    # Check API connectivity
    api_connected = False
    try:
        api_client = get_api_client()
        response = await api_client.get("/health")
        api_connected = response.status_code == 200
        details["api_status"] = str(response.status_code)
    except Exception as e:
        details["api_error"] = str(e)
        logger.warning(f"API health check failed: {e}")

    # Check AI Coach connectivity
    ai_coach_connected = False
    try:
        ai_coach_client = get_ai_coach_client()
        response = await ai_coach_client.get("/health")
        ai_coach_connected = response.status_code == 200
        details["ai_coach_status"] = str(response.status_code)
    except Exception as e:
        details["ai_coach_error"] = str(e)
        logger.warning(f"AI Coach health check failed: {e}")

    # Determine overall status
    if redis_connected and api_connected and ai_coach_connected:
        status = "healthy"
    elif redis_connected:
        status = "degraded"
    else:
        status = "unhealthy"

    return HealthResponse(
        status=status,
        redis_connected=redis_connected,
        queue_depth=queue_depth,
        api_connected=api_connected,
        ai_coach_connected=ai_coach_connected,
        details=details,
    )


@app.get("/")
async def root():
    """Root endpoint redirect to health."""
    return {"message": "Worker health check server. See /health for status."}
