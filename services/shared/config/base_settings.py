"""Base configuration utilities for all services."""

from enum import Enum


class LogLevel(str, Enum):
    """Log level enumeration for consistent logging configuration."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


def build_redis_url(host: str = "localhost", port: int = 6379, db: int = 0, password: str | None = None) -> str:
    """Build a Redis connection URL.

    Args:
        host: Redis host
        port: Redis port
        db: Redis database number
        password: Optional Redis password

    Returns:
        Redis connection URL string
    """
    if password:
        return f"redis://:{password}@{host}:{port}/{db}"
    return f"redis://{host}:{port}/{db}"
