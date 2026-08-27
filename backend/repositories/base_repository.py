"""Shared repository behaviour.

Subclasses inherit the execute helpers and row-mapping utilities, which keeps
cursor and transaction boilerplate in one place and lets each repository consist
of little more than its own SQL.
"""

from __future__ import annotations

from typing import Any, Callable, Mapping, Sequence, TypeVar

from database.connection import read_only, transaction

T = TypeVar("T")


class BaseRepository:
    """Thin wrapper over the connection helpers.

    Reads run inside a read-only transaction that always rolls back; writes run
    inside a transaction that commits on success. Every method is static, so a
    repository can be constructed cheaply per request without holding state.
    """

    @staticmethod
    def fetch_one(sql: str, params: Mapping[str, Any] | None = None) -> dict[str, Any] | None:
        """Execute a query and return its first row.

        Args:
            sql: Statement using named placeholders.
            params: Values bound to the placeholders.

        Returns:
            The first row as a plain dictionary, or None if nothing matched.

        Raises:
            psycopg2.Error: If the statement fails.
        """
        with read_only() as cursor:
            cursor.execute(sql, params or {})
            row = cursor.fetchone()
            return dict(row) if row is not None else None

    @staticmethod
    def fetch_all(sql: str, params: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
        """Execute a query and return every row.

        Args:
            sql: Statement using named placeholders.
            params: Values bound to the placeholders.

        Returns:
            The rows as plain dictionaries, empty when nothing matched.

        Raises:
            psycopg2.Error: If the statement fails.
        """
        with read_only() as cursor:
            cursor.execute(sql, params or {})
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def fetch_scalar(
        sql: str, params: Mapping[str, Any] | None = None, *, column: str, default: Any = None
    ) -> Any:
        """Execute a query and return one column of its first row.

        Args:
            sql: Statement using named placeholders.
            params: Values bound to the placeholders.
            column: Name of the column to read.
            default: Returned when nothing matched.

        Returns:
            The column value, or ``default``.

        Raises:
            psycopg2.Error: If the statement fails.
            KeyError: If the row lacks that column.
        """
        with read_only() as cursor:
            cursor.execute(sql, params or {})
            row = cursor.fetchone()
            return row[column] if row is not None else default

    @staticmethod
    def execute(sql: str, params: Mapping[str, Any] | None = None) -> int:
        """Execute a statement inside a transaction.

        Args:
            sql: Statement using named placeholders.
            params: Values bound to the placeholders.

        Returns:
            The number of affected rows.

        Raises:
            psycopg2.Error: If the statement fails; the transaction is rolled
                back first.
        """
        with transaction() as cursor:
            cursor.execute(sql, params or {})
            return cursor.rowcount

    @staticmethod
    def execute_returning(
        sql: str, params: Mapping[str, Any] | None = None
    ) -> dict[str, Any] | None:
        """Execute a statement with RETURNING and read one row.

        Args:
            sql: Statement ending in ``RETURNING``.
            params: Values bound to the placeholders.

        Returns:
            The returned row, or None when the statement affected none. A None
            result is meaningful: it usually means a guard such as
            ``ON CONFLICT DO NOTHING`` or a status precondition matched nothing.

        Raises:
            psycopg2.Error: If the statement fails.
        """
        with transaction() as cursor:
            cursor.execute(sql, params or {})
            row = cursor.fetchone()
            return dict(row) if row is not None else None

    @staticmethod
    def map_one(
        row: dict[str, Any] | None, factory: Callable[[Mapping[str, Any]], T]
    ) -> T | None:
        """Map an optional row to a domain model.

        Args:
            row: The row, or None.
            factory: Callable building the model, normally a ``from_row``.

        Returns:
            The model, or None.
        """
        return factory(row) if row is not None else None

    @staticmethod
    def map_all(
        rows: Sequence[Mapping[str, Any]], factory: Callable[[Mapping[str, Any]], T]
    ) -> list[T]:
        """Map a sequence of rows to domain models.

        Args:
            rows: The rows.
            factory: Callable building each model.

        Returns:
            The models, in the order given.
        """
        return [factory(row) for row in rows]
