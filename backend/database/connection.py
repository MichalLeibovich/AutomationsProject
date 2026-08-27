"""psycopg2 connection pooling and transaction helpers.

A pool is used rather than a connection per request because establishing a
PostgreSQL connection costs several milliseconds plus a backend process.
``RealDictCursor`` is configured globally so rows arrive as mappings and
repositories can address columns by name.
"""

from __future__ import annotations

import threading
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import psycopg2
import psycopg2.extras
from psycopg2 import pool as pg_pool
from psycopg2.extensions import connection as PgConnection

from config.config import get_config
from utils.errors import ServiceUnavailableError
from utils.logger import get_logger

logger = get_logger(__name__)

_pool: pg_pool.ThreadedConnectionPool | None = None
_lock = threading.Lock()


def init_pool() -> pg_pool.ThreadedConnectionPool:
    """Create the process-wide connection pool.

    Idempotent and thread-safe. Called at startup so a bad DSN stops the process
    at boot rather than on the first request.

    Returns:
        The initialised pool.

    Raises:
        ServiceUnavailableError: If the pool cannot be created, for example
            because the database is unreachable or the DSN is invalid.
    """
    global _pool

    with _lock:
        if _pool is not None:
            return _pool

        settings = get_config().database
        try:
            _pool = pg_pool.ThreadedConnectionPool(
                minconn=settings.min_connections,
                maxconn=settings.max_connections,
                dsn=settings.dsn,
                cursor_factory=psycopg2.extras.RealDictCursor,
                options=f"-c statement_timeout={settings.statement_timeout_ms}",
                application_name=get_config().logging.service_name,
            )
        except psycopg2.Error as exc:
            logger.error("failed to initialise connection pool: %s", exc)
            raise ServiceUnavailableError("בסיס הנתונים אינו זמין") from exc

        logger.info(
            "connection pool ready",
            extra={"min": settings.min_connections, "max": settings.max_connections},
        )
        return _pool


def get_pool() -> pg_pool.ThreadedConnectionPool:
    """Return the pool, creating it if necessary.

    Returns:
        The process-wide pool.

    Raises:
        ServiceUnavailableError: If it has to be created and cannot be.
    """
    return _pool if _pool is not None else init_pool()


def close_pool() -> None:
    """Close every pooled connection and discard the pool.

    Called on shutdown so PostgreSQL backends are released promptly rather than
    waiting to time out.
    """
    global _pool

    with _lock:
        if _pool is not None:
            _pool.closeall()
            _pool = None
            logger.info("connection pool closed")


@contextmanager
def get_connection() -> Iterator[PgConnection]:
    """Borrow a connection from the pool.

    Always returned, including when the body raises.

    Yields:
        A pooled connection. Transaction state is the caller's responsibility;
        prefer :func:`transaction` or :func:`read_only`.

    Raises:
        psycopg2.Error: Propagated after being logged.
    """
    pool = get_pool()
    conn: PgConnection | None = None

    try:
        conn = pool.getconn()
        yield conn
    except psycopg2.Error as exc:
        logger.error("database error: %s", exc)
        raise
    finally:
        if conn is not None:
            pool.putconn(conn)


@contextmanager
def transaction() -> Iterator[psycopg2.extras.RealDictCursor]:
    """Run a write transaction.

    Commits on clean exit, rolls back on any exception. Every mutation goes
    through this.

    Yields:
        A cursor bound to the transaction.

    Raises:
        Exception: Any exception raised in the body, after the rollback.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()


@contextmanager
def read_only() -> Iterator[psycopg2.extras.RealDictCursor]:
    """Run a read-only transaction.

    Always rolls back rather than committing, which releases the snapshot and
    stops connections lingering idle-in-transaction.

    Yields:
        A cursor bound to the transaction.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            yield cursor
        finally:
            cursor.close()
            conn.rollback()


@contextmanager
def server_side_cursor(
    name: str, itersize: int = 1000
) -> Iterator[psycopg2.extras.RealDictCursor]:
    """Open a named cursor that streams rows from the server.

    Used for large result sets such as CSV export, where materialising every row
    in memory is unacceptable.

    Args:
        name: Cursor name, unique within the connection.
        itersize: Rows fetched per network round trip.

    Yields:
        A named cursor; iterating it streams rows in batches.
    """
    with get_connection() as conn:
        cursor = conn.cursor(name=name)
        cursor.itersize = itersize
        try:
            yield cursor
        finally:
            cursor.close()
            conn.rollback()


def apply_schema(schema_path: Path | None = None) -> None:
    """Execute the schema file against the configured database.

    The statements are idempotent, so repeated application is safe. Requires a
    role that may create schemas, extensions and tables.

    Args:
        schema_path: Path to the SQL file. Defaults to ``schema.sql`` beside this
            module.

    Raises:
        psycopg2.Error: If any statement fails.
        OSError: If the file cannot be read.
    """
    path = schema_path or Path(__file__).with_name("schema.sql")
    sql = path.read_text(encoding="utf-8")

    with get_connection() as conn:
        # Autocommit, because some statements cannot run inside a transaction
        # block.
        previous = conn.autocommit
        conn.autocommit = True
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql)
        finally:
            conn.autocommit = previous

    logger.info("schema applied", extra={"path": str(path)})


def healthcheck() -> bool:
    """Test whether the database answers a trivial query.

    Used by the readiness probe, so it never raises.

    Returns:
        True if the database responded, False on any failure.
    """
    try:
        with read_only() as cursor:
            cursor.execute("SELECT 1 AS ok")
            return cursor.fetchone() is not None
    except Exception as exc:
        logger.warning("database healthcheck failed: %s", exc)
        return False
