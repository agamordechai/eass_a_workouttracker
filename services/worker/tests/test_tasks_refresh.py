"""Tests for refresh task."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.anyio
async def test_refresh_exercises_success():
    """Test successful exercise refresh."""
    from services.worker.src.tasks.refresh import refresh_exercises

    # Mock ExerciseRefresher
    mock_refresher = MagicMock()
    mock_refresher.refresh_all = AsyncMock()
    mock_refresher.get_summary.return_value = {
        "processed": 10,
        "skipped": 5,
        "failed": 0,
        "total": 15,
        "success_rate": 100.0,
    }

    with patch("services.worker.src.tasks.refresh.ExerciseRefresher") as MockRefresher:
        MockRefresher.return_value.__aenter__.return_value = mock_refresher

        result = await refresh_exercises({})

        assert result["processed"] == 10
        assert result["skipped"] == 5
        assert result["failed"] == 0
        assert result["total"] == 15
        assert result["success_rate"] == 100.0


@pytest.mark.anyio
async def test_refresh_exercises_with_failures():
    """Test exercise refresh with some failures."""
    from services.worker.src.tasks.refresh import refresh_exercises

    mock_refresher = MagicMock()
    mock_refresher.refresh_all = AsyncMock()
    mock_refresher.get_summary.return_value = {
        "processed": 8,
        "skipped": 3,
        "failed": 2,
        "total": 13,
        "success_rate": 84.6,
    }

    with patch("services.worker.src.tasks.refresh.ExerciseRefresher") as MockRefresher:
        MockRefresher.return_value.__aenter__.return_value = mock_refresher

        result = await refresh_exercises({})

        assert result["processed"] == 8
        assert result["failed"] == 2
        assert result["success_rate"] == 84.6


@pytest.mark.anyio
async def test_refresh_exercises_config():
    """Test that refresh task uses correct configuration."""
    from dev.refresh import RefreshConfig
    from services.worker.src.tasks.refresh import refresh_exercises

    with patch("services.worker.src.tasks.refresh.ExerciseRefresher") as MockRefresher:
        mock_refresher = MagicMock()
        mock_refresher.refresh_all = AsyncMock()
        mock_refresher.get_summary.return_value = {
            "processed": 0,
            "skipped": 0,
            "failed": 0,
            "total": 0,
            "success_rate": 0,
        }
        MockRefresher.return_value.__aenter__.return_value = mock_refresher

        await refresh_exercises({})

        # Verify RefreshConfig was created
        assert MockRefresher.called
        call_args = MockRefresher.call_args[0][0]
        assert isinstance(call_args, RefreshConfig)
