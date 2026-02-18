"""Tests for worker entry point."""

from services.worker.src.worker import WorkerSettings


def test_worker_settings_redis():
    """Test worker Redis settings configuration."""
    assert WorkerSettings.redis_settings.host is not None
    assert WorkerSettings.redis_settings.port is not None
    assert WorkerSettings.redis_settings.database is not None


def test_worker_settings_functions():
    """Test worker task functions are registered."""
    assert len(WorkerSettings.functions) == 3

    function_names = [f.__name__ for f in WorkerSettings.functions]
    assert "refresh_exercises" in function_names
    assert "warmup_ai_cache" in function_names
    assert "cleanup_stale_data" in function_names


def test_worker_settings_cron_jobs():
    """Test worker cron jobs are configured."""
    # At least one cron job should be enabled by default
    assert len(WorkerSettings.cron_jobs) >= 1


def test_worker_settings_limits():
    """Test worker job limits."""
    assert WorkerSettings.max_jobs > 0
    assert WorkerSettings.job_timeout > 0


def test_worker_settings_hooks():
    """Test worker lifecycle hooks."""
    assert WorkerSettings.on_startup is not None
    assert WorkerSettings.on_shutdown is not None
