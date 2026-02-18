from pydantic import Field
from pydantic_settings import BaseSettings


class RateLimitSettings(BaseSettings):
    """Rate limit configuration."""

    enabled: bool = Field(default=True)
    redis_url: str = Field(default="redis://redis:6379/2")

    # Limits per minute
    public_limit: str = Field(default="100/minute")
    auth_limit: str = Field(default="10/minute")
    read_limit_anonymous: str = Field(default="60/minute")
    read_limit_user: str = Field(default="120/minute")
    read_limit_admin: str = Field(default="300/minute")
    write_limit_anonymous: str = Field(default="30/minute")
    write_limit_user: str = Field(default="60/minute")
    write_limit_admin: str = Field(default="150/minute")
    admin_limit: str = Field(default="100/minute")

    class Config:
        env_prefix = "RATELIMIT_"


_settings = None


def get_ratelimit_settings() -> RateLimitSettings:
    """Get cached rate limit settings instance."""
    global _settings
    if _settings is None:
        _settings = RateLimitSettings()
    return _settings
