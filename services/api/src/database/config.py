"""Configuration settings for the Workout Tracker API."""
import os
from pathlib import Path
from typing import Optional, Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration settings.

    Supports both PostgreSQL (via DATABASE_URL) and SQLite (via path).
    PostgreSQL is used when DATABASE_URL is set.

    Attributes:
        url: PostgreSQL connection URL (e.g., postgresql://user:pass@host:port/db)
        path: Path to the SQLite database file (fallback if url not set)
        echo_sql: Whether to echo SQL statements (useful for debugging)
        pool_size: Connection pool size
        timeout: Database connection timeout in seconds
    """

    url: Optional[str] = Field(
        default=None,
        description="PostgreSQL database URL (overrides path if set)"
    )
    path: Path = Field(
        default=Path("data/workout_tracker.db"),
        description="Path to the SQLite database file (used if url not set)"
    )
    echo_sql: bool = Field(
        default=False,
        description="Echo SQL statements for debugging"
    )
    pool_size: int = Field(
        default=5,
        ge=1,
        le=100,
        description="Database connection pool size"
    )
    timeout: float = Field(
        default=5.0,
        ge=0.1,
        description="Database connection timeout in seconds"
    )

    def __init__(self, **data):
        """Initialize database settings, checking DATABASE_URL env var."""
        # Check for DATABASE_URL environment variable
        if 'url' not in data:
            data['url'] = os.environ.get('DATABASE_URL')
        super().__init__(**data)

    @property
    def is_postgres(self) -> bool:
        """Check if using PostgreSQL."""
        return self.url is not None and self.url.startswith('postgresql')

    @field_validator('path')
    @classmethod
    def ensure_absolute_path(cls, v: Path) -> Path:
        """Convert relative paths to absolute paths."""
        if not v.is_absolute():
            # Resolve relative to project root (services/api/src/database -> project root)
            project_root = Path(__file__).parent.parent.parent.parent.parent
            v = (project_root / v).resolve()
        return v

    model_config = SettingsConfigDict(
        env_prefix='DB_',
        case_sensitive=False,
        extra='ignore'
    )


class APISettings(BaseSettings):
    """API server configuration settings.

    Attributes:
        host: Host address to bind the server
        port: Port number to listen on
        debug: Enable debug mode
        reload: Enable auto-reload on code changes (development only)
        workers: Number of worker processes
        title: API title
        description: API description
        version: API version
        docs_url: URL path for API documentation (set to None to disable)
        openapi_url: URL path for OpenAPI schema (set to None to disable)
    """

    host: str = Field(
        default="0.0.0.0",
        description="Host address to bind the server"
    )
    port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Port number to listen on"
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    reload: bool = Field(
        default=False,
        description="Enable auto-reload on code changes"
    )
    workers: int = Field(
        default=1,
        ge=1,
        description="Number of worker processes"
    )
    title: str = Field(
        default="Workout Tracker",
        description="API title"
    )
    description: str = Field(
        default="A simple workout tracker app",
        description="API description"
    )
    version: str = Field(
        default="0.1.0",
        description="API version"
    )
    docs_url: Optional[str] = Field(
        default="/docs",
        description="URL path for API documentation"
    )
    openapi_url: Optional[str] = Field(
        default="/openapi.json",
        description="URL path for OpenAPI schema"
    )

    model_config = SettingsConfigDict(
        env_prefix='API_',
        case_sensitive=False,
        extra='ignore'
    )


class AppSettings(BaseSettings):
    """Application-wide configuration settings.

    This is the main settings class that combines all configuration sections.
    Settings can be overridden via environment variables (with APP_ prefix)
    or by creating a .env file.

    Attributes:
        db: Database configuration
        api: API server configuration
        log_level: Logging level
        cors_origins: Allowed CORS origins (comma-separated)
        enable_metrics: Enable metrics collection
    """

    # Nested configuration sections
    db: Optional[DatabaseSettings] = None
    api: Optional[APISettings] = None

    def __init__(self, **data):
        """Initialize settings and ensure nested settings use the same env file."""
        # Extract _env_file if provided
        env_file = data.pop('_env_file', None)

        # Initialize nested settings with the same env file if not already provided
        if 'db' not in data:
            data['db'] = DatabaseSettings(_env_file=env_file) if env_file else DatabaseSettings()
        if 'api' not in data:
            data['api'] = APISettings(_env_file=env_file) if env_file else APISettings()

        # Call parent init
        super().__init__(**data)

    # Application-level settings
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level"
    )
    cors_origins: str = Field(
        default="*",
        description="Allowed CORS origins (comma-separated)"
    )
    enable_metrics: bool = Field(
        default=False,
        description="Enable metrics collection"
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]

    def ensure_data_directory(self) -> None:
        """Ensure the database directory exists."""
        db_dir = self.db.path.parent
        db_dir.mkdir(parents=True, exist_ok=True)

    model_config = SettingsConfigDict(
        env_prefix='APP_',
        env_file_encoding='utf-8',
        env_nested_delimiter='__',
        case_sensitive=False,
        extra='ignore'
    )


# Singleton instance of settings
_settings: Optional[AppSettings] = None


def get_settings() -> AppSettings:
    """Get the application settings singleton.

    This function returns a cached settings instance to avoid repeated
    file reads and environment variable lookups. The settings are loaded
    from environment variables with optional .env file support.

    Settings hierarchy (lowest to highest priority):
        1. Default values in Pydantic models
        2. .env file (if exists in working directory)
        3. Environment variables

    Returns:
        AppSettings: The application settings instance containing:
            - db: DatabaseSettings (path, timeout, pool_size, echo_sql)
            - api: APISettings (host, port, debug, workers, title, version)
            - log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            - cors_origins: CORS allowed origins
            - enable_metrics: Metrics collection flag

    Example:
        >>> settings = get_settings()
        >>> print(settings.api.port)
        8000
        >>> print(settings.db.path)
        PosixPath('/app/data/workout_tracker.db')
    """
    global _settings
    if _settings is None:
        # Load .env file if it exists (for local overrides)
        env_file = Path('.env')

        if env_file.exists():
            _settings = AppSettings(_env_file=env_file)
        else:
            _settings = AppSettings()

        # Ensure data directory exists
        _settings.ensure_data_directory()

    return _settings


def reload_settings() -> AppSettings:
    """Force reload of application settings.

    Useful for testing or when configuration changes need to be picked up
    without restarting the application.

    Returns:
        AppSettings: The newly loaded settings instance
    """
    global _settings
    _settings = None
    return get_settings()

