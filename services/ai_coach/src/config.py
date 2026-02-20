"""Configuration settings for the AI Coach service."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class AISettings(BaseSettings):
    """AI model configuration."""

    model: str = Field(default="anthropic:claude-haiku-4-5", description="AI model to use")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Model temperature")
    max_tokens: int = Field(default=1024, ge=1, description="Max tokens in response")


class APIClientSettings(BaseSettings):
    """Workout API client configuration."""

    base_url: str = Field(default="http://api:8000", description="Workout API base URL")
    timeout: float = Field(default=10.0, description="Request timeout in seconds")


class RedisSettings(BaseSettings):
    """Redis configuration for caching."""

    url: str = Field(default="redis://redis:6379/0", description="Redis connection URL")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")


class ServiceSettings(BaseSettings):
    """Service configuration."""

    host: str = Field(default="0.0.0.0", description="Service host")
    port: int = Field(default=8001, description="Service port")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Log level")


class Settings(BaseSettings):
    """Main settings aggregating all configuration."""

    # AI settings
    ai_model: str = Field(default="anthropic:claude-haiku-4-5", alias="AI_MODEL")
    ai_temperature: float = Field(default=0.7, alias="AI_TEMPERATURE")

    # Anthropic API key
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")

    # Workout API
    workout_api_url: str = Field(default="http://api:8000", alias="WORKOUT_API_URL")

    # Redis
    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")
    cache_ttl: int = Field(default=3600, alias="CACHE_TTL")

    # JWT (shared with API for admin-check on per-user keys)
    jwt_secret_key: str = Field(default="dev-secret-key-change-in-production", alias="JWT_SECRET_KEY")

    # Service
    host: str = Field(default="0.0.0.0", alias="SERVICE_HOST")
    port: int = Field(default=8001, alias="SERVICE_PORT")
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
