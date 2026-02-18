"""Tests for the database configuration."""

from _pytest.monkeypatch import MonkeyPatch

from services.api.src.database.config import APISettings, AppSettings, DatabaseSettings, get_settings, reload_settings


def test_database_settings_defaults() -> None:
    """Verify DatabaseSettings initializes with correct default values.

    Tests that a DatabaseSettings instance created without arguments uses
    the expected default values for path, echo_sql, pool_size, and timeout.

    Asserts:
        - Database path name is "workout_tracker.db"
        - SQL echo is disabled by default
        - Connection pool size is 5
        - Connection timeout is 5.0 seconds
    """
    db_settings = DatabaseSettings()

    assert db_settings.path.name == "workout_tracker.db"
    assert db_settings.echo_sql is False
    assert db_settings.pool_size == 5
    assert db_settings.timeout == 5.0


def test_database_settings_from_env(monkeypatch: MonkeyPatch) -> None:
    """Verify DatabaseSettings loads correctly from environment variables.

    Tests that DatabaseSettings properly reads and converts environment
    variables with the DB_ prefix, including type conversion for booleans,
    integers, and floats.

    Args:
        monkeypatch: Pytest fixture for safely patching environment variables.

    Setup:
        Sets DB_PATH, DB_ECHO_SQL, DB_POOL_SIZE, and DB_TIMEOUT environment
        variables to custom test values.

    Asserts:
        - Path is correctly set to custom value
        - Boolean is properly parsed from string "true"
        - Integer is correctly converted from string "10"
        - Float is correctly converted from string "15.0"
    """
    monkeypatch.setenv("DB_PATH", "/custom/path/test.db")
    monkeypatch.setenv("DB_ECHO_SQL", "true")
    monkeypatch.setenv("DB_POOL_SIZE", "10")
    monkeypatch.setenv("DB_TIMEOUT", "15.0")

    db_settings = DatabaseSettings()

    assert str(db_settings.path) == "/custom/path/test.db"
    assert db_settings.echo_sql is True
    assert db_settings.pool_size == 10
    assert db_settings.timeout == 15.0


def test_api_settings_defaults() -> None:
    """Verify APISettings initializes with correct default values.

    Tests that an APISettings instance created without arguments uses
    the expected default values for host, port, debug mode, and API metadata.

    Asserts:
        - Host is "0.0.0.0"
        - Port is 8000
        - Debug mode is disabled
        - API title is "Workout Tracker"
    """
    api_settings = APISettings()

    assert api_settings.host == "0.0.0.0"
    assert api_settings.port == 8000
    assert api_settings.debug is False
    assert api_settings.title == "Workout Tracker"


def test_app_settings_cors_origins_list() -> None:
    """Verify cors_origins_list property parses origins correctly.

    Tests that the cors_origins_list property correctly handles both
    wildcard (*) and comma-separated origin strings.

    Asserts:
        - Wildcard "*" returns ["*"]
        - Comma-separated origins are split correctly
    """
    settings = AppSettings(cors_origins="*")
    assert settings.cors_origins_list == ["*"]

    settings = AppSettings(cors_origins="http://localhost:3000, http://example.com")
    assert settings.cors_origins_list == ["http://localhost:3000", "http://example.com"]


def test_get_settings_returns_singleton() -> None:
    """Verify get_settings returns the same instance on multiple calls.

    Tests that the settings singleton pattern works correctly by comparing
    instances from multiple get_settings() calls.

    Asserts:
        - Multiple calls to get_settings() return the same object instance.
    """
    settings1 = get_settings()
    settings2 = get_settings()

    assert settings1 is settings2


def test_reload_settings_creates_new_instance() -> None:
    """Verify reload_settings creates a fresh settings instance.

    Tests that calling reload_settings() creates a new settings object,
    allowing configuration changes to be picked up.

    Asserts:
        - reload_settings returns a valid AppSettings instance
        - The returned instance is functional (has expected attributes)
    """
    get_settings()  # ensure settings are cached
    reloaded = reload_settings()

    # Should return a settings instance
    assert isinstance(reloaded, AppSettings)
    assert reloaded.db is not None
    assert reloaded.api is not None
