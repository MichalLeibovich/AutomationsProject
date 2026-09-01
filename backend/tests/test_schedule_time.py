"""Unit tests for schedule occurrence arithmetic, in particular DST handling.

The spring-forward and fall-back transition instants are *discovered* from
``zoneinfo`` itself rather than hardcoded, so these tests stay correct
regardless of which year they run in or any change to Israel's DST rule.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from utils.schedule_time import (
    build_idempotency_key,
    next_occurrence,
    occurrences_between,
    parse_idempotency_key,
)

JERUSALEM = "Asia/Jerusalem"


def _find_transition(year: int, month: int) -> datetime:
    """Locate the hour a UTC offset change happens in Asia/Jerusalem.

    Scans hour by hour through the given month for the boundary where
    ``utcoffset()`` differs from the previous hour.

    Args:
        year: Year to scan.
        month: Month to scan; the caller picks one known to contain a
            transition (March for spring-forward, October for fall-back).

    Returns:
        The UTC instant of the last hour *before* the offset changes.

    Raises:
        AssertionError: If no transition is found in the month, which would
            mean the test's assumption about Israel's DST calendar is stale.
    """
    tz = ZoneInfo(JERUSALEM)
    cursor = datetime(year, month, 1, tzinfo=UTC)
    end = cursor + timedelta(days=31)
    previous_offset = cursor.astimezone(tz).utcoffset()

    while cursor < end:
        offset = cursor.astimezone(tz).utcoffset()
        if offset != previous_offset:
            return cursor - timedelta(hours=1)
        previous_offset = offset
        cursor += timedelta(hours=1)

    raise AssertionError(f"no DST transition found in {year}-{month:02d}")


def test_spring_forward_gap_produces_no_occurrence() -> None:
    """A schedule anchored at :00 must not fire during the skipped hour."""
    before_transition = _find_transition(2026, 3)  # last pre-transition hour, UTC
    local_before = before_transition.astimezone(ZoneInfo(JERUSALEM))
    gap_start_local = local_before.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)

    window_start = before_transition - timedelta(hours=6)
    window_end = before_transition + timedelta(hours=6)

    occurrences = occurrences_between(
        every_hours=1,
        anchor_minute=0,
        timezone=JERUSALEM,
        start_utc=window_start,
        end_utc=window_end,
    )

    local_occurrences = [instant.astimezone(ZoneInfo(JERUSALEM)) for instant in occurrences]
    local_labels = {(dt.hour, dt.minute) for dt in local_occurrences}

    # The gap's wall-clock label must be entirely absent...
    assert (gap_start_local.hour, gap_start_local.minute) not in local_labels
    # ...but nothing else is skipped. Local wall-clock time advances 13 hours
    # over this 12-real-hour window (it jumps forward through the gap), so an
    # hourly rule would naively touch 13 local labels; one is missing, leaving
    # 12 — exactly the real-hour span, since the lost label and the extra
    # local hour cancel out.
    expected_count = int((window_end - window_start).total_seconds() // 3600)
    assert len(occurrences) == expected_count


def test_fall_back_ambiguous_hour_fires_exactly_once() -> None:
    """A schedule anchored at :00 must fire once, not twice, on the repeated hour."""
    before_transition = _find_transition(2026, 10)
    local_before = before_transition.astimezone(ZoneInfo(JERUSALEM))
    repeated_local = local_before.replace(minute=0, second=0, microsecond=0)

    window_start = before_transition - timedelta(hours=6)
    window_end = before_transition + timedelta(hours=6)

    occurrences = occurrences_between(
        every_hours=1,
        anchor_minute=0,
        timezone=JERUSALEM,
        start_utc=window_start,
        end_utc=window_end,
    )

    matches = [
        instant
        for instant in occurrences
        if instant.astimezone(ZoneInfo(JERUSALEM)).replace(tzinfo=None)
        == repeated_local.replace(tzinfo=None)
    ]

    # Exactly one physical instant was generated for the repeated label...
    assert len(matches) == 1
    # ...and it is the earlier (pre-transition, fold=0) of the two real instants.
    assert matches[0] == before_transition.replace(minute=0, second=0, microsecond=0)

    # Local wall-clock time advances only 11 hours over this 12-real-hour
    # window (it falls back through the repeated hour), so an hourly rule
    # touches only 11 distinct local labels — each firing exactly once,
    # including the repeated one, which is why this is 12 - 1 rather than 12.
    expected_count = int((window_end - window_start).total_seconds() // 3600) - 1
    assert len(occurrences) == expected_count


def test_ordinary_day_produces_evenly_spaced_occurrences() -> None:
    """Sanity check well away from any transition: no surprises, no gaps."""
    start = datetime(2026, 6, 1, tzinfo=UTC)
    end = datetime(2026, 6, 2, tzinfo=UTC)

    occurrences = occurrences_between(
        every_hours=2, anchor_minute=0, timezone=JERUSALEM, start_utc=start, end_utc=end
    )

    assert len(occurrences) == 12
    gaps = {b - a for a, b in zip(occurrences, occurrences[1:])}
    assert gaps == {timedelta(hours=2)}


def test_pending_change_keeps_the_pivot_occurrence_then_switches_cadence() -> None:
    """Worked example: a 2-hour schedule changes to a 3-hour one. The
    occurrence that was already next (the pivot) fires unchanged, and only
    occurrences after it follow the new cadence."""
    pivot = datetime(2026, 6, 1, 19, 0, tzinfo=UTC)  # 22:00 Asia/Jerusalem (IDT, UTC+3)
    start = pivot - timedelta(hours=1)  # 21:00 local, after the run that already happened at 20:00
    end = pivot + timedelta(hours=7)  # room for two 3-hour steps past the pivot

    occurrences = occurrences_between(
        every_hours=2,
        anchor_minute=0,
        timezone=JERUSALEM,
        start_utc=start,
        end_utc=end,
        pending_every_hours=3,
        pending_effective_after=pivot,
    )

    assert occurrences == [
        pivot,  # 22:00 — produced by the old 2-hour cadence, untouched
        pivot + timedelta(hours=3),  # 01:00 — new 3-hour cadence counts from the pivot
        pivot + timedelta(hours=6),  # 04:00
    ]
    # The old cadence's 00:00/02:00 slots (pivot + 2h/4h) must not appear —
    # the new cadence fully replaces it after the pivot.
    assert pivot + timedelta(hours=2) not in occurrences
    assert pivot + timedelta(hours=4) not in occurrences


def test_pending_change_produces_nothing_before_the_pivot_is_reached() -> None:
    """Querying a window that ends before the pivot only sees the old grid,
    same as if no change were pending at all."""
    pivot = datetime(2026, 6, 1, 19, 0, tzinfo=UTC)
    start = pivot - timedelta(hours=3)
    end = pivot - timedelta(hours=1)

    with_pending = occurrences_between(
        every_hours=2,
        anchor_minute=0,
        timezone=JERUSALEM,
        start_utc=start,
        end_utc=end,
        pending_every_hours=3,
        pending_effective_after=pivot,
    )
    without_pending = occurrences_between(
        every_hours=2, anchor_minute=0, timezone=JERUSALEM, start_utc=start, end_utc=end
    )

    assert with_pending == without_pending


def test_pending_change_far_in_the_past_still_computes_a_far_future_window() -> None:
    """Once the pivot itself is long gone, the new cadence alone must still
    describe the grid correctly — no reliance on iterating from the pivot."""
    pivot = datetime(2026, 1, 1, tzinfo=UTC)
    start = datetime(2026, 6, 1, tzinfo=UTC)
    end = start + timedelta(hours=6)

    occurrences = occurrences_between(
        every_hours=2,
        anchor_minute=0,
        timezone=JERUSALEM,
        start_utc=start,
        end_utc=end,
        pending_every_hours=4,
        pending_effective_after=pivot,
    )

    assert len(occurrences) == 2
    assert (occurrences[0] - pivot) % timedelta(hours=4) == timedelta(0)
    gaps = {b - a for a, b in zip(occurrences, occurrences[1:])}
    assert gaps == {timedelta(hours=4)}


def test_next_occurrence_with_pending_change_returns_the_pivot() -> None:
    pivot = datetime(2026, 6, 1, 19, 0, tzinfo=UTC)
    after = pivot - timedelta(hours=1, minutes=30)  # 20:30 local, mirrors the worked example

    result = next_occurrence(
        every_hours=2,
        anchor_minute=0,
        timezone=JERUSALEM,
        after_utc=after,
        pending_every_hours=3,
        pending_effective_after=pivot,
    )

    assert result == pivot


def test_every_hours_must_be_positive() -> None:
    with pytest.raises(ValueError):
        occurrences_between(
            every_hours=0,
            anchor_minute=0,
            timezone=JERUSALEM,
            start_utc=datetime(2026, 1, 1, tzinfo=UTC),
            end_utc=datetime(2026, 1, 2, tzinfo=UTC),
        )


def test_next_occurrence_finds_the_first_one_after_a_given_instant() -> None:
    after = datetime(2026, 6, 1, 1, 30, tzinfo=UTC)  # 04:30 Asia/Jerusalem (IDT, UTC+3)

    result = next_occurrence(
        every_hours=2, anchor_minute=0, timezone=JERUSALEM, after_utc=after
    )

    assert result == datetime(2026, 6, 1, 3, 0, tzinfo=UTC)  # 06:00 Asia/Jerusalem


class TestIdempotencyKeyRoundTrip:
    """The idempotency key is the only durable record of a run's occurrence."""

    def test_schedule_key_round_trips(self) -> None:
        from uuid import uuid4

        schedule_id = uuid4()
        occurrence = datetime(2026, 9, 1, 1, 0, 0, tzinfo=UTC)

        key = build_idempotency_key(kind="schedule", entity_id=schedule_id, occurrence=occurrence)
        origin = parse_idempotency_key(key)

        assert origin is not None
        assert origin.kind == "schedule"
        assert origin.schedule_id == schedule_id
        assert origin.extra_run_id is None
        assert origin.occurrence == occurrence

    def test_extra_key_round_trips(self) -> None:
        from uuid import uuid4

        extra_id = uuid4()
        occurrence = datetime(2026, 9, 1, 13, 45, 0, tzinfo=UTC)

        key = build_idempotency_key(kind="extra", entity_id=extra_id, occurrence=occurrence)
        origin = parse_idempotency_key(key)

        assert origin is not None
        assert origin.kind == "extra"
        assert origin.extra_run_id == extra_id
        assert origin.schedule_id is None
        assert origin.occurrence == occurrence

    def test_non_schedule_key_parses_to_none(self) -> None:
        assert parse_idempotency_key("a1b2c3d4e5f6") is None
        assert parse_idempotency_key(None) is None
        assert parse_idempotency_key("manual-abc123") is None

    def test_malformed_schedule_key_parses_to_none(self) -> None:
        assert parse_idempotency_key("schedule:not-a-uuid:123") is None
        assert parse_idempotency_key("schedule:") is None
