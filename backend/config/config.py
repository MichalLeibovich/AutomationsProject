"""Environment-backed application configuration.

Exposed as frozen dataclasses grouped by concern, so a consumer depends only on
the section it needs and cannot mutate settings at runtime.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

def _require(name: str) -> str:
    """Read a mandatory environment variable.

    Args:
        name: Environment variable name.

    Returns:
        The variable's value.

    Raises:
        RuntimeError: If the variable is unset or empty.
    """
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _as_int(name: str, default: int) -> int:
    """Read an integer environment variable.

    Args:
        name: Environment variable name.
        default: Value returned when unset or empty.

    Returns:
        The parsed integer, or ``default``.
    """
    raw = os.environ.get(name)
    return int(raw) if raw else default


def _as_bool(name: str, default: bool = False) -> bool:
    """Read a boolean environment variable.

    Args:
        name: Environment variable name.
        default: Value returned when unset.

    Returns:
        True for ``1``, ``true``, ``yes`` or ``on``, case-insensitive.
    """
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _as_list(name: str) -> list[str]:
    """Read a comma-separated environment variable.

    Args:
        name: Environment variable name.

    Returns:
        The trimmed, non-empty values.
    """
    return [item.strip() for item in os.environ.get(name, "").split(",") if item.strip()]


@dataclass(frozen=True)
class DatabaseConfig:
    """PostgreSQL connection settings.

    Attributes:
        dsn: libpq connection string.
        min_connections: Connections opened eagerly by the pool.
        max_connections: Upper bound on pooled connections.
        statement_timeout_ms: Server-side timeout, so a runaway query cannot
            occupy a pool slot indefinitely.
    """

    dsn: str
    min_connections: int = 2
    max_connections: int = 10
    statement_timeout_ms: int = 15_000


@dataclass(frozen=True)
class LoggingConfig:
    """Structured logging settings.

    Attributes:
        level: Root logger level name.
        service_name: Value emitted in the ``service`` log field, also used as
            the PostgreSQL application name.
    """

    level: str = "INFO"
    service_name: str = "noc-api"


@dataclass(frozen=True)
class Config:
    """Complete application configuration.

    Attributes:
        env: Deployment environment name.
        debug: Whether Flask debug mode is on.
        host: Interface the development server binds to.
        port: Port the development server binds to.
        database: Database settings.
        logging: Logging settings.
        cors_origins: Origins permitted to call the API.
        artifacts_dir: Directory the runner writes artifacts into, served back
            through the API.
        default_page_size: Page size applied when a request omits one.
        max_page_size: Largest page size a request may ask for.
        retention_months: Months of run history kept before partitions are
            dropped.
    """

    env: str
    debug: bool
    host: str
    port: int
    database: DatabaseConfig
    logging: LoggingConfig
    cors_origins: list[str] = field(default_factory=list)
    artifacts_dir: str = "./artifacts"
    default_page_size: int = 60
    max_page_size: int = 200
    retention_months: int = 24

    @property
    def is_production(self) -> bool:
        """Whether this process runs in the production environment."""
        return self.env == "production"


@lru_cache(maxsize=1)
def get_config() -> Config:
    """Build the configuration from the environment.

    Cached, so the environment is read once per process and every caller sees
    identical settings.

    Returns:
        The populated configuration.

    Raises:
        RuntimeError: If ``DATABASE_URL`` is unset.
    """
    env = os.environ.get("APP_ENV", "development")

    return Config(
        env=env,
        debug=_as_bool("FLASK_DEBUG", env == "development"),
        host=os.environ.get("HOST", "0.0.0.0"),
        port=_as_int("PORT", 8000),
        database=DatabaseConfig(
            dsn=_require("DATABASE_URL"),
            min_connections=_as_int("DB_POOL_MIN", 2),
            max_connections=_as_int("DB_POOL_MAX", 10),
            statement_timeout_ms=_as_int("DB_STATEMENT_TIMEOUT_MS", 15_000),
        ),
        logging=LoggingConfig(
            level=os.environ.get("LOG_LEVEL", "INFO"),
            service_name=os.environ.get("SERVICE_NAME", "noc-api"),
        ),
        cors_origins=_as_list("CORS_ORIGINS"),
        artifacts_dir=os.environ.get("ARTIFACTS_DIR", "./artifacts"),
        retention_months=_as_int("RETENTION_MONTHS", 24),
    )
