"""Tests for cleanup task."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.anyio
async def test_cleanup_stale_data_success():
    """Test successful cleanup."""
    from services.worker.src.tasks.cleanup import REDIS_AVAILABLE, cleanup_stale_data

    if not REDIS_AVAILABLE:
        pytest.skip("Redis not available")

    # Mock Redis client
    mock_redis = MagicMock()
    mock_redis.ping = AsyncMock()
    mock_redis.scan = AsyncMock(
        side_effect=[
            # First scan returns some keys
            (10, ["idempotency:refresh:1:2026-01-01", "idempotency:refresh:2:2026-01-01"]),
            # Second scan returns no more keys
            (0, []),
        ]
    )
    mock_redis.ttl = AsyncMock(return_value=-1)  # No TTL (should be deleted)
    mock_redis.delete = AsyncMock()
    mock_redis.aclose = AsyncMock()

    with patch("services.worker.src.tasks.cleanup.redis.from_url", return_value=mock_redis):
        result = await cleanup_stale_data({})

        assert result["deleted_idempotency_keys"] == 2
        assert result["cleanup_time_ms"] >= 0


@pytest.mark.anyio
async def test_cleanup_stale_data_no_deletions():
    """Test cleanup when all keys have valid TTL."""
    from services.worker.src.tasks.cleanup import REDIS_AVAILABLE, cleanup_stale_data

    if not REDIS_AVAILABLE:
        pytest.skip("Redis not available")

    mock_redis = MagicMock()
    mock_redis.ping = AsyncMock()
    mock_redis.scan = AsyncMock(
        side_effect=[
            (10, ["idempotency:refresh:1:2026-01-01"]),
            (0, []),
        ]
    )
    mock_redis.ttl = AsyncMock(return_value=3600)  # Valid TTL (should not be deleted)
    mock_redis.delete = AsyncMock()
    mock_redis.aclose = AsyncMock()

    with patch("services.worker.src.tasks.cleanup.redis.from_url", return_value=mock_redis):
        result = await cleanup_stale_data({})

        assert result["deleted_idempotency_keys"] == 0
        mock_redis.delete.assert_not_called()


@pytest.mark.anyio
async def test_cleanup_stale_data_redis_error():
    """Test cleanup handles Redis errors gracefully."""
    from services.worker.src.tasks.cleanup import REDIS_AVAILABLE, cleanup_stale_data

    if not REDIS_AVAILABLE:
        pytest.skip("Redis not available")

    mock_redis = MagicMock()
    mock_redis.ping = AsyncMock(side_effect=Exception("Connection failed"))
    mock_redis.aclose = AsyncMock()

    with patch("services.worker.src.tasks.cleanup.redis.from_url", return_value=mock_redis):
        result = await cleanup_stale_data({})

        assert result["deleted_idempotency_keys"] == 0
        assert result["cleanup_time_ms"] == 0


@pytest.mark.anyio
async def test_cleanup_stale_data_no_redis():
    """Test cleanup when Redis is not available."""
    from services.worker.src.tasks.cleanup import cleanup_stale_data

    with patch("services.worker.src.tasks.cleanup.REDIS_AVAILABLE", False):
        result = await cleanup_stale_data({})

        assert result["deleted_idempotency_keys"] == 0
        assert result["cleanup_time_ms"] == 0
