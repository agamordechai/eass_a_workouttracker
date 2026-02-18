"""HTTP clients for API and AI Coach services."""

import httpx

from .config import get_settings

# Module-level singleton instances
_api_client: httpx.AsyncClient | None = None
_ai_coach_client: httpx.AsyncClient | None = None


def get_api_client() -> httpx.AsyncClient:
    """Get singleton API client instance."""
    global _api_client
    if _api_client is None:
        settings = get_settings()
        _api_client = httpx.AsyncClient(
            base_url=settings.api_client__workout_api_url,
            timeout=settings.api_client__timeout,
            headers={"User-Agent": "grindlogger-worker"},
        )
    return _api_client


def get_ai_coach_client() -> httpx.AsyncClient:
    """Get singleton AI Coach client instance."""
    global _ai_coach_client
    if _ai_coach_client is None:
        settings = get_settings()
        _ai_coach_client = httpx.AsyncClient(
            base_url=settings.api_client__ai_coach_url,
            timeout=settings.api_client__timeout,
            headers={"User-Agent": "grindlogger-worker"},
        )
    return _ai_coach_client


async def close_clients() -> None:
    """Close all HTTP clients."""
    global _api_client, _ai_coach_client
    if _api_client:
        await _api_client.aclose()
        _api_client = None
    if _ai_coach_client:
        await _ai_coach_client.aclose()
        _ai_coach_client = None
