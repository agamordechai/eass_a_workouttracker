"""Base HTTP client for service-to-service communication.

This module provides a base client class with common functionality for
making HTTP requests to other services in the workout tracker system.
"""

import logging

import httpx

logger = logging.getLogger(__name__)


class BaseAPIClient:
    """Base HTTP client for API communication.

    Provides common functionality for:
    - Connection management
    - Health checks
    - Timeouts
    - Async context management
    """

    def __init__(self, base_url: str, timeout: float = 10.0, headers: dict | None = None):
        """Initialize the API client.

        Args:
            base_url: Base URL of the target API
            timeout: Request timeout in seconds
            headers: Optional default headers for all requests
        """
        self.base_url = base_url
        self.timeout = timeout
        self.default_headers = headers or {}
        self._client: httpx.AsyncClient | None = None

    async def get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client.

        Returns:
            Configured AsyncClient instance
        """
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout, headers=self.default_headers)
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def health_check(self, endpoint: str = "/health") -> bool:
        """Check if the target API is healthy.

        Args:
            endpoint: Health check endpoint path

        Returns:
            True if API is healthy, False otherwise
        """
        try:
            client = await self.get_client()
            response = await client.get(endpoint)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Health check failed for {self.base_url}: {e}")
            return False

    async def __aenter__(self):
        """Async context manager entry."""
        await self.get_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
