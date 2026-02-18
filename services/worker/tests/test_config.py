"""Tests for worker configuration."""

from services.worker.src.config import Settings, get_settings


def test_default_settings():
    """Test default settings values."""
    settings = Settings()

    assert settings.log_level == "INFO"
    assert settings.redis__host == "localhost"
    assert settings.redis__port == 6379
    assert settings.redis__database == 1
    assert settings.redis__cache_database == 0
    assert settings.api_client__workout_api_url == "http://localhost:8000"
    assert settings.api_client__ai_coach_url == "http://localhost:8001"
    assert settings.worker__max_jobs == 10
    assert settings.worker__job_timeout == 300
    assert settings.worker__health_port == 8002


def test_redis_queue_url():
    """Test Redis queue URL generation."""
    settings = Settings(
        redis__host="redis",
        redis__port=6379,
        redis__database=1,
    )

    assert settings.redis_queue_url == "redis://redis:6379/1"


def test_redis_queue_url_with_password():
    """Test Redis queue URL with password."""
    settings = Settings(
        redis__host="redis",
        redis__port=6379,
        redis__database=1,
        redis__password="secret",
    )

    assert settings.redis_queue_url == "redis://:secret@redis:6379/1"


def test_redis_cache_url():
    """Test Redis cache URL generation."""
    settings = Settings(
        redis__host="redis",
        redis__port=6379,
        redis__cache_database=0,
    )

    assert settings.redis_cache_url == "redis://redis:6379/0"


def test_schedule_settings():
    """Test schedule configuration."""
    settings = Settings()

    assert settings.schedule__enable_hourly_refresh is True
    assert settings.schedule__enable_daily_warmup is True
    assert settings.schedule__enable_weekly_cleanup is True
    assert settings.schedule__warmup_hour == 6
    assert settings.schedule__cleanup_day_of_week == 6
    assert settings.schedule__cleanup_hour == 2


def test_refresh_settings():
    """Test refresh configuration."""
    settings = Settings()

    assert settings.refresh__concurrency == 5
    assert settings.refresh__idempotency_ttl == 3600
    assert settings.refresh__retry_delay == 5
    assert settings.refresh__max_retries == 3


def test_get_settings_cached():
    """Test that get_settings returns cached instance."""
    settings1 = get_settings()
    settings2 = get_settings()

    assert settings1 is settings2
