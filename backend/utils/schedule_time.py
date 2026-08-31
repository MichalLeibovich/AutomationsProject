"""Pure schedule-occurrence arithmetic.

Occurrences are never stored — every list of "when does this schedule fire" is
recomputed from the rule (``every_hours``, ``anchor_minute``, ``timezone``) on
demand. Keeping that computation here, free of any database or Flask import,
is what makes the DST behaviour directly unit-testable.

The idempotency key a scheduled run is created with doubles as the durable
record of which occurrence produced it — :func:`build_idempotency_key` and
:func:`parse_idempotency_key` are the two halves of that encoding. See
``ScheduleService`` for how it is used both to prevent double-firing and, much
later, to answer "which slot did this run belong to" for the history view,
with no extra column on ``test_runs``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo

SCHEDULE_PREFIX = "schedule"
EXTRA_PREFIX = "extra"
"""Idempotency-key prefixes distinguishing a recurring occurrence from a
one-off :class:`~database.models.ScheduleExtraRun`."""


def occurrences_between(
    *,
    every_hours: int,
    anchor_minute: int,
    timezone: str,
    start_utc: datetime,
    end_utc: datetime,
) -> list[datetime]:
    """List every occurrence of a recurring rule in ``[start_utc, end_utc)``.

    Occurrences are defined on the *local* wall clock in ``timezone`` — every
    ``every_hours`` hours starting from local midnight, at ``anchor_minute``
    past the hour — then converted to UTC. Stepping happens in naive local
    time rather than UTC or aware-local time, which is what keeps a DST
    transition from distorting the step size: a ``timedelta(hours=2)`` step
    taken in aware-local time silently drifts by an hour across a transition,
    since the same wall-clock step spans a different number of real hours.

    A local wall-clock time that does not exist (the spring-forward gap)
    produces no occurrence — the slot is simply absent, not shifted to the
    nearest valid time. A local wall-clock time that occurs twice (the
    autumn fall-back) produces exactly one occurrence, anchored to its first
    (pre-transition) physical instant: the naive-time loop only ever visits
    each wall-clock label once, so a second occurrence for the same label
    cannot be generated.

    Args:
        every_hours: Interval between occurrences, in hours. Must be
            positive.
        anchor_minute: Minute past each hour the schedule fires on, 0-59.
        timezone: IANA zone name the rule is defined against, for example
            ``"Asia/Jerusalem"``.
        start_utc: Range start, inclusive.
        end_utc: Range end, exclusive.

    Returns:
        Occurrence instants as timezone-aware UTC datetimes, ascending. Empty
        if the range contains none.

    Raises:
        ValueError: If ``every_hours`` is not positive, or ``end_utc`` is not
            after ``start_utc``.
    """
    if every_hours <= 0:
        raise ValueError("every_hours must be positive")
    if end_utc <= start_utc:
        raise ValueError("end_utc must be after start_utc")

    tz = ZoneInfo(timezone)
    step = timedelta(hours=every_hours)

    # Naive local time is the coordinate system the rule is actually defined
    # in. Starting from local midnight of the start day guarantees every
    # candidate in range is visited even when the first one falls before
    # `start_utc` — such candidates are simply filtered out below.
    local_start = start_utc.astimezone(tz)
    naive_cursor = local_start.replace(
        hour=0, minute=anchor_minute, second=0, microsecond=0, tzinfo=None
    )
    naive_end = end_utc.astimezone(tz).replace(tzinfo=None)

    results: list[datetime] = []

    while naive_cursor < naive_end + timedelta(days=1):
        candidate = naive_cursor.replace(tzinfo=tz, fold=0)

        # A nonexistent local time (spring-forward gap) round-trips to a
        # different wall-clock label than we asked for, because fold=0
        # resolves it using the pre-transition offset and the transition
        # then pushes the resulting instant out the other side of the gap.
        # An ambiguous-but-real local time (fall-back) round-trips cleanly,
        # since it genuinely exists — just twice — and fold=0 deterministically
        # picks the earlier of the two.
        roundtrip = candidate.astimezone(UTC).astimezone(tz).replace(tzinfo=None)

        if roundtrip == naive_cursor:
            candidate_utc = candidate.astimezone(UTC)
            if start_utc <= candidate_utc < end_utc:
                results.append(candidate_utc)
        # else: the gap swallows this slot. No occurrence is generated for
        # it, and none is generated later to compensate.

        naive_cursor += step

    return results


def next_occurrence(
    *, every_hours: int, anchor_minute: int, timezone: str, after_utc: datetime, horizon_hours: int = 24
) -> datetime | None:
    """Find the next occurrence strictly after a given instant.

    Args:
        every_hours: Interval between occurrences, in hours.
        anchor_minute: Minute past each hour the schedule fires on.
        timezone: IANA zone name the rule is defined against.
        after_utc: Only occurrences after this instant are considered.
        horizon_hours: How far ahead to search before giving up. Must exceed
            ``every_hours``, or a schedule could have no occurrence within
            the search window at all.

    Returns:
        The next occurrence, or None if none falls within ``horizon_hours``.
    """
    window_end = after_utc + timedelta(hours=horizon_hours)
    for occurrence in occurrences_between(
        every_hours=every_hours,
        anchor_minute=anchor_minute,
        timezone=timezone,
        start_utc=after_utc + timedelta(seconds=1),
        end_utc=window_end,
    ):
        return occurrence
    return None


@dataclass(frozen=True, slots=True)
class ScheduleOrigin:
    """What a scheduled run's idempotency key says about where it came from.

    Attributes:
        kind: ``"schedule"`` for a recurring rule's occurrence, ``"extra"``
            for a one-off :class:`~database.models.ScheduleExtraRun`.
        schedule_id: The recurring rule, when ``kind == "schedule"``.
        extra_run_id: The one-off run, when ``kind == "extra"``.
        occurrence: The UTC instant this run was enqueued for — the slot it
            belongs to, independent of when the row was actually created.
    """

    kind: Literal["schedule", "extra"]
    schedule_id: UUID | None
    extra_run_id: UUID | None
    occurrence: datetime


def build_idempotency_key(
    *, kind: Literal["schedule", "extra"], entity_id: UUID, occurrence: datetime
) -> str:
    """Build the idempotency key a scheduled run is created with.

    The occurrence is encoded as whole epoch seconds rather than an ISO
    timestamp specifically so the key can be split on ``:`` unambiguously —
    an ISO instant contains colons of its own, which would make a plain
    ``split(":")`` misparse it.

    Args:
        kind: ``"schedule"`` or ``"extra"``.
        entity_id: The schedule or extra-run identifier.
        occurrence: The UTC instant this run is being created for.

    Returns:
        A key of the form ``"{kind}:{entityId}:{epochSeconds}"``.
    """
    epoch_seconds = int(occurrence.astimezone(UTC).timestamp())
    return f"{kind}:{entity_id}:{epoch_seconds}"


def parse_idempotency_key(idempotency_key: str | None) -> ScheduleOrigin | None:
    """Recover a run's scheduled origin from its idempotency key.

    This is the entire mechanism behind associating a ``test_runs`` row with
    the scheduled occurrence that produced it — no ``scheduled_for`` column
    is needed, because the occurrence was already encoded in the key at
    enqueue time and is frozen on the run row from then on, unaffected by how
    late the run actually started executing.

    Args:
        idempotency_key: The run's stored key, or None.

    Returns:
        The parsed origin, or None if the key was not produced by the
        scheduler (a manual, bulk, CI or API run has its own key shape).
    """
    if not idempotency_key:
        return None

    parts = idempotency_key.split(":")
    if len(parts) != 3:
        return None

    kind, raw_id, raw_epoch = parts
    if kind not in (SCHEDULE_PREFIX, EXTRA_PREFIX):
        return None

    try:
        entity_id = UUID(raw_id)
        occurrence = datetime.fromtimestamp(int(raw_epoch), tz=UTC)
    except (ValueError, OverflowError, OSError):
        return None

    return ScheduleOrigin(
        kind=kind,  # type: ignore[arg-type]
        schedule_id=entity_id if kind == SCHEDULE_PREFIX else None,
        extra_run_id=entity_id if kind == EXTRA_PREFIX else None,
        occurrence=occurrence,
    )
