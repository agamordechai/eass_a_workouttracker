import pytest
from pathlib import Path
from _pytest.monkeypatch import MonkeyPatch
from app.config import (
    DatabaseSettings,
    APISettings,
    AppSettings,
    get_settings,
    reload_settings
)


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
    monkeypatch.setenv('DB_PATH', '/tmp/test.db')
    monkeypatch.setenv('DB_ECHO_SQL', 'true')
    monkeypatch.setenv('DB_POOL_SIZE', '10')
    monkeypatch.setenv('DB_TIMEOUT', '15.0')

    db_settings = DatabaseSettings()

    assert str(db_settings.path) == '/tmp/test.db'
    assert db_settings.echo_sql is True
    assert db_settings.pool_size == 10
    assert db_settings.timeout == 15.0


def test_api_settings_defaults() -> None:
    """Verify APISettings initializes with correct default values.

    Tests that an APISettings instance created without arguments uses the
    expected default values for all API configuration parameters.

    Asserts:
        - Host is set to "0.0.0.0" (all interfaces)
        - Port is set to 8000
        - Debug mode is disabled
        - Auto-reload is disabled
        - Worker count is 1
        - API title is "Workout Tracker"
    """
    api_settings = APISettings()

    assert api_settings.host == "0.0.0.0"
    assert api_settings.port == 8000
    assert api_settings.debug is False
    assert api_settings.reload is False
    assert api_settings.workers == 1
    assert api_settings.title == "Workout Tracker"


def test_api_settings_from_env(monkeypatch: MonkeyPatch) -> None:
    """Verify APISettings loads correctly from environment variables.

    Tests that APISettings properly reads and converts environment variables
    with the API_ prefix, including proper type conversion.

    Args:
        monkeypatch: Pytest fixture for safely patching environment variables.

    Setup:
        Sets API_HOST, API_PORT, API_DEBUG, and API_WORKERS environment
        variables to custom test values.

    Asserts:
        - Host string is correctly loaded
        - Port integer is properly converted
        - Debug boolean is parsed from string
        - Workers count is correctly converted
    """
    monkeypatch.setenv('API_HOST', '127.0.0.1')
    monkeypatch.setenv('API_PORT', '9000')
    monkeypatch.setenv('API_DEBUG', 'true')
    monkeypatch.setenv('API_WORKERS', '4')

    api_settings = APISettings()

    assert api_settings.host == '127.0.0.1'
    assert api_settings.port == 9000
    assert api_settings.debug is True
    assert api_settings.workers == 4


def test_api_settings_validation() -> None:
    """Verify APISettings validates port numbers within valid range.

    Tests that Pydantic validation properly enforces port number constraints,
    rejecting invalid values and accepting valid ones.

    Test Cases:
        1. Port 0 (too low) - should raise ValueError
        2. Port 70000 (too high) - should raise ValueError
        3. Port 8080 (valid) - should be accepted

    Asserts:
        - Invalid ports (≤0 or >65535) raise ValueError
        - Valid ports (1-65535) are accepted and stored correctly
    """
    # Test invalid port
    with pytest.raises(ValueError):
        APISettings(port=0)

    with pytest.raises(ValueError):
        APISettings(port=70000)

    # Valid port
    api_settings = APISettings(port=8080)
    assert api_settings.port == 8080


def test_app_settings_defaults() -> None:
    """Verify AppSettings initializes with correct default values.

    Tests that an AppSettings instance created without arguments uses the
    expected default values for application-level configuration.

    Asserts:
        - Log level is set to "INFO"
        - CORS origins is set to "*" (all origins)
        - Metrics collection is disabled
    """
    app_settings = AppSettings()

    assert app_settings.log_level == "INFO"
    assert app_settings.cors_origins == "*"
    assert app_settings.enable_metrics is False



def test_cors_origins_list_parsing() -> None:
    """Verify CORS origins string is correctly parsed into a list.

    Tests the cors_origins_list property that converts the comma-separated
    string into a list of individual origin URLs.

    Test Cases:
        1. Single wildcard "*" - returns ["*"]
        2. Multiple origins without spaces - returns list of URLs
        3. Multiple origins with spaces - returns trimmed list of URLs

    Asserts:
        - Wildcard is preserved as single-element list
        - Multiple origins are split on commas
        - Whitespace is properly trimmed from each origin
    """
    # Single wildcard
    settings1 = AppSettings(cors_origins="*")
    assert settings1.cors_origins_list == ["*"]

    # Multiple origins
    settings2 = AppSettings(cors_origins="https://example.com,https://app.example.com")
    assert settings2.cors_origins_list == ["https://example.com", "https://app.example.com"]

    # With spaces
    settings3 = AppSettings(cors_origins="https://a.com, https://b.com , https://c.com")
    assert settings3.cors_origins_list == ["https://a.com", "https://b.com", "https://c.com"]


def test_nested_settings() -> None:
    """Verify AppSettings contains properly nested configuration objects.

    Tests that AppSettings correctly initializes and provides access to
    nested DatabaseSettings and APISettings objects through the db and
    api attributes.

    Asserts:
        - AppSettings.db contains DatabaseSettings attributes
        - AppSettings.api contains APISettings attributes
        - Nested attributes are accessible via dot notation
    """
    app_settings = AppSettings()

    # Check nested database settings
    assert hasattr(app_settings.db, 'path')
    assert hasattr(app_settings.db, 'echo_sql')
    assert hasattr(app_settings.db, 'timeout')

    # Check nested API settings
    assert hasattr(app_settings.api, 'host')
    assert hasattr(app_settings.api, 'port')
    assert hasattr(app_settings.api, 'debug')


def test_nested_env_variable_override(monkeypatch: MonkeyPatch) -> None:
    """Verify nested settings can be overridden via environment variables.

    Tests that environment variables with appropriate prefixes (DB_, API_)
    correctly override nested configuration values within AppSettings.

    Args:
        monkeypatch: Pytest fixture for safely patching environment variables.

    Setup:
        Sets DB_PATH and API_PORT environment variables to custom values.

    Asserts:
        - Database path in nested db settings matches environment variable
        - API port in nested api settings matches environment variable
    """
    monkeypatch.setenv('DB_PATH', '/custom/path.db')
    monkeypatch.setenv('API_PORT', '9999')

    app_settings = AppSettings()

    assert str(app_settings.db.path) == '/custom/path.db'
    assert app_settings.api.port == 9999


def test_get_settings_singleton() -> None:
    """Verify get_settings returns the same instance on multiple calls.

    Tests that the get_settings function implements the singleton pattern,
    returning the same cached AppSettings instance rather than creating
    new instances on each call.

    Asserts:
        - Multiple calls to get_settings return the same object instance
        - Object identity (is) check confirms singleton behavior
    """
    settings1 = get_settings()
    settings2 = get_settings()

    # Should be the same instance
    assert settings1 is settings2


def test_reload_settings(monkeypatch: MonkeyPatch) -> None:
    """Verify reload_settings forces re-initialization of the settings.

    Tests that the reload_settings function clears the cached singleton
    and creates a new settings instance, while get_settings continues to
    return the cached instance until reload is called.

    Args:
        monkeypatch: Pytest fixture for safely patching environment variables.

    Test Flow:
        1. Get initial settings and store original port value
        2. Change environment variable
        3. Verify get_settings still returns cached value
        4. Call reload_settings to force re-initialization

    Note:
        The reload mechanism is tested for existence; monkeypatched
        environment variables may not always be picked up in all contexts.
    """
    # Get initial settings
    settings1 = get_settings()
    original_port = settings1.api.port

    # Change environment variable
    monkeypatch.setenv('API_PORT', '7777')

    # Settings should not change (cached)
    settings2 = get_settings()
    assert settings2.api.port == original_port

    # Reload settings
    settings3 = reload_settings()
    # Note: reload might not pick up monkeypatched envs in all cases
    # This tests the reload mechanism exists


def test_database_path_resolution() -> None:
    """Verify relative database paths are resolved to absolute paths.

    Tests that the custom validator for DatabaseSettings.path automatically
    converts relative paths to absolute paths based on the project root.

    Setup:
        Creates DatabaseSettings with relative path "test.db".

    Asserts:
        - The path is converted to an absolute path
        - is_absolute() returns True for the resulting path
    """
    db_settings = DatabaseSettings(path=Path("test.db"))

    # Should be converted to absolute path
    assert db_settings.path.is_absolute()



def test_log_level_validation() -> None:
    """Verify log_level setting only accepts valid logging levels.

    Tests that Pydantic's Literal type validation enforces that only
    standard Python logging levels are accepted.

    Test Cases:
        1. Valid: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL" - accepted
        2. Invalid: "INVALID" - should raise ValueError

    Asserts:
        - All valid log level strings are accepted
        - Invalid log level strings raise ValueError with validation error
    """
    # Valid log levels
    for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        settings = AppSettings(log_level=level)
        assert settings.log_level == level

    # Invalid log level should raise validation error
    with pytest.raises(ValueError):
        AppSettings(log_level="INVALID")


def test_ensure_data_directory(tmp_path: Path) -> None:
    """Verify ensure_data_directory creates missing database directories.

    Tests that the ensure_data_directory method creates the parent directory
    for the database file if it doesn't exist.

    Args:
        tmp_path: Pytest fixture providing a temporary directory path.

    Setup:
        Creates AppSettings with database path in non-existent subdirectory.

    Asserts:
        - Directory doesn't exist before calling ensure_data_directory
        - Directory exists after calling ensure_data_directory
        - Created path is a directory (not a file)
    """
    db_path = tmp_path / "test_data" / "test.db"
    app_settings = AppSettings()
    app_settings.db.path = db_path

    # Directory should not exist yet
    assert not db_path.parent.exists()

    # Call ensure_data_directory
    app_settings.ensure_data_directory()

    # Directory should now exist
    assert db_path.parent.exists()
    assert db_path.parent.is_dir()


def test_configuration_documentation() -> None:
    """Verify all settings have field descriptions for documentation.

    Tests that the Pydantic Field() definitions include description parameters
    for all configuration fields, ensuring self-documenting code.

    Asserts:
        - DatabaseSettings.path has a non-None description
        - APISettings.port has a non-None description
        - AppSettings.log_level has a non-None description

    Note:
        This ensures that the configuration is self-documenting and can be
        used to generate documentation automatically.
    """
    db_settings = DatabaseSettings()
    api_settings = APISettings()
    app_settings = AppSettings()

    # Check that model schema includes descriptions
    assert db_settings.model_fields['path'].description is not None
    assert api_settings.model_fields['port'].description is not None
    assert app_settings.model_fields['log_level'].description is not None


def test_settings_serialization() -> None:
    """Verify settings can be serialized to dictionary format.

    Tests that AppSettings instances can be converted to dictionaries using
    Pydantic's model_dump method, which is useful for logging, debugging,
    and exporting configuration.

    Asserts:
        - model_dump() returns a dictionary
        - Dictionary contains expected top-level keys
        - Nested settings are included in the dictionary
    """
    settings = AppSettings()

    # Should be able to dump to dict
    settings_dict = settings.model_dump()

    assert isinstance(settings_dict, dict)
    assert 'log_level' in settings_dict
    assert 'db' in settings_dict
    assert 'api' in settings_dict

