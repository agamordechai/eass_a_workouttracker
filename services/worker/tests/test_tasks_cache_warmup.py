"""Tests for cache warmup task."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.anyio
async def test_warmup_ai_cache_success():
    """Test successful AI cache warmup."""
    from services.worker.src.tasks.cache_warmup import warmup_ai_cache

    # Mock httpx client
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()

    mock_client = MagicMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    with patch("services.worker.src.tasks.cache_warmup.get_ai_coach_client", return_value=mock_client):
        result = await warmup_ai_cache({})

        # Should make requests for all combinations
        # 7 muscle groups * 5 equipment combos * 4 durations = 140 requests
        assert result["total_requests"] == 140
        assert result["successful"] == 140
        assert result["failed"] == 0


@pytest.mark.anyio
async def test_warmup_ai_cache_with_failures():
    """Test AI cache warmup with some failures."""
    from services.worker.src.tasks.cache_warmup import warmup_ai_cache

    call_count = 0

    async def mock_post(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        # Fail every 10th request
        if call_count % 10 == 0:
            raise Exception("API error")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        return mock_response

    mock_client = MagicMock()
    mock_client.post = mock_post

    with patch("services.worker.src.tasks.cache_warmup.get_ai_coach_client", return_value=mock_client):
        result = await warmup_ai_cache({})

        assert result["total_requests"] == 140
        assert result["failed"] == 14  # Every 10th request fails
        assert result["successful"] == 126


@pytest.mark.anyio
async def test_warmup_ai_cache_request_format():
    """Test that warmup requests have correct format."""
    from services.worker.src.tasks.cache_warmup import warmup_ai_cache

    requests_made = []

    async def capture_post(*args, **kwargs):
        requests_made.append(kwargs.get("json"))
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        return mock_response

    mock_client = MagicMock()
    mock_client.post = capture_post

    with patch("services.worker.src.tasks.cache_warmup.get_ai_coach_client", return_value=mock_client):
        result = await warmup_ai_cache({})

        # Verify at least one request was captured
        assert len(requests_made) > 0

        # Check first request format
        first_request = requests_made[0]
        assert "focus_area" in first_request
        assert "equipment_available" in first_request
        assert "session_duration_minutes" in first_request
        assert isinstance(first_request["equipment_available"], list)
        assert isinstance(first_request["session_duration_minutes"], int)
