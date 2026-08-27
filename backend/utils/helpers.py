"""Pure helper functions.

Free of I/O and framework imports, so every function here is directly
unit-testable.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, Iterable, Iterator, Mapping, TypeVar

from utils.constants import BUCKET_DAY, BUCKET_HOUR, BUCKET_MINUTE

T = TypeVar("T")


def to_camel_case(snake: str) -> str:
    """Convert a snake_case identifier to camelCase.

    Args:
        snake: Identifier such as ``"started_at"``.

    Returns:
        The camelCase form, such as ``"startedAt"``.
    """
    head, *rest = snake.split("_")
    return head + "".join(word.capitalize() for word in rest)


def keys_to_camel_case(row: Mapping[str, Any]) -> dict[str, Any]:
    """Rewrite a mapping's keys from snake_case to camelCase.

    Column names stay snake_case in SQL while the JSON contract stays camelCase.

    Args:
        row: Mapping with snake_case keys.

    Returns:
        A new dictionary with camelCase keys.
    """
    return {to_camel_case(key): value for key, value in row.items()}


def iso(value: datetime | None) -> str | None:
    """Render a datetime as ISO 8601.

    Args:
        value: The datetime, or None.

    Returns:
        The ISO representation, or None.
    """
    return value.isoformat() if value is not None else None


def pass_rate(total: int, failed: int) -> int:
    """Compute a whole-percent pass rate.

    Args:
        total: Total runs.
        failed: Runs that failed.

    Returns:
        The rate rounded to the nearest percent. Zero runs yields 0 rather than
        raising on a division by zero.
    """
    if total <= 0:
        return 0
    return round(((total - failed) / total) * 100)


def resolve_range(
    preset: str, date_from: datetime | None, date_to: datetime | None
) -> tuple[datetime, datetime, str]:
    """Resolve a range preset into concrete bounds and a bucket size.

    Each range gets a granularity that yields a readable number of points: the
    last hour in five-minute steps, a day hourly, a week daily. Bucketing an hour
    by the hour, as this once did, produces a chart with one bar.

    Args:
        preset: ``"hour"``, ``"day"``, ``"week"`` or ``"custom"``. An
            unrecognised value falls back to ``"week"``.
        date_from: Start bound, required only for ``"custom"``.
        date_to: End bound, required only for ``"custom"``.

    Returns:
        Start bound, end bound and bucket granularity.

    Raises:
        ValueError: If ``preset`` is ``"custom"`` and a bound is missing.
    """
    now = datetime.now(UTC)

    if preset == "custom":
        if date_from is None or date_to is None:
            raise ValueError("custom range requires both bounds")
        end_of_day = date_to.replace(hour=23, minute=59, second=59, microsecond=0)
        return date_from, end_of_day, BUCKET_DAY

    windows: dict[str, tuple[timedelta, str]] = {
        "hour": (timedelta(hours=1), BUCKET_MINUTE),
        "day": (timedelta(days=1), BUCKET_HOUR),
        "week": (timedelta(days=7), BUCKET_DAY),
    }
    delta, bucket = windows.get(preset, windows["week"])
    return now - delta, now, bucket


def bucket_label(value: datetime, bucket: str) -> str:
    """Format a chart axis label for a time bucket.

    Args:
        value: The bucket's start instant.
        bucket: ``"minute"``, ``"hour"`` or ``"day"``.

    Returns:
        ``"14:05"`` for a five-minute bucket, ``"14:00"`` for an hourly one, or
        ``"5.8"`` for a daily one.
    """
    if bucket == BUCKET_MINUTE:
        return f"{value.hour:02d}:{value.minute:02d}"
    if bucket == BUCKET_HOUR:
        return f"{value.hour:02d}:00"
    return f"{value.day}.{value.month}"


def chunked(items: Iterable[T], size: int) -> Iterator[list[T]]:
    """Split an iterable into consecutive batches.

    Args:
        items: Source iterable, consumed lazily.
        size: Maximum batch length.

    Yields:
        Lists of at most ``size`` items; the last may be shorter.
    """
    batch: list[T] = []
    for item in items:
        batch.append(item)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch


def first_of_month(year: int, month: int) -> datetime:
    """Midnight UTC on the first day of a month.

    Args:
        year: Four-digit year.
        month: Month number, 1 to 12.

    Returns:
        A timezone-aware datetime.
    """
    return datetime(year, month, 1, tzinfo=UTC)


def start_of_next_month(year: int, month: int) -> datetime:
    """Midnight UTC on the first day of the following month.

    Args:
        year: Four-digit year.
        month: Month number; December rolls into January of ``year + 1``.

    Returns:
        A timezone-aware datetime.
    """
    return first_of_month(year + 1, 1) if month == 12 else first_of_month(year, month + 1)
