"""Unit tests for ScheduleService.tick, against fake repositories.

No database is involved: the repositories and run service are mocked, so
these tests exercise only the orchestration logic — which occurrences get
enqueued, which are skipped, and what idempotency key each is given.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from database.models import Schedule, ScheduleExtraRun, ScheduleSkip, TestDefinition
from services.schedule_service import ScheduleService
from utils.errors import NotFoundError
from utils.schedule_time import build_idempotency_key


def _make_definition(application_id) -> TestDefinition:
    return TestDefinition(
        id=uuid4(),
        application_id=application_id,
        scope="application",
        kind="main",
        name="בדיקת שפיות",
        description=None,
        runner_target="harmony_automations/tests/test_smoke.py::test_site_is_reachable",
        display_order=0,
        timeout_seconds=600,
        is_active=True,
    )


def _service(**overrides) -> tuple[ScheduleService, dict]:
    application_id = uuid4()
    schedule = Schedule(
        id=uuid4(),
        application_id=application_id,
        every_hours=2,
        anchor_minute=0,
        timezone="Asia/Jerusalem",
        is_active=True,
        application_name="הרמוניה",
    )
    definition = _make_definition(application_id)

    schedules_repo = MagicMock()
    schedules_repo.list_active.return_value = [schedule]
    schedules_repo.list_skips_in_range.return_value = overrides.get("skips", [])
    schedules_repo.list_due_extra_runs.return_value = overrides.get("extras", [])

    definitions_repo = MagicMock()
    definitions_repo.find_main_for_application.return_value = definition

    run_service = MagicMock()
    run_service.was_already_created.return_value = False

    service = ScheduleService(
        schedule_repository=schedules_repo,
        definition_repository=definitions_repo,
        application_repository=MagicMock(),
        run_service=run_service,
    )
    return service, {
        "schedule": schedule,
        "definition": definition,
        "run_service": run_service,
        "schedules_repo": schedules_repo,
    }


def test_tick_enqueues_the_one_occurrence_due_in_the_lookback_window() -> None:
    # 04:00 Asia/Jerusalem (IDT, UTC+3) on an ordinary June day == 01:00Z.
    now = datetime(2026, 6, 1, 1, 0, 5, tzinfo=UTC)
    service, ctx = _service()

    result = service.tick(now=now)

    assert result == {"enqueued": 1}
    ctx["run_service"].start_run.assert_called_once()
    call = ctx["run_service"].start_run.call_args.kwargs
    assert call["definition_id"] == ctx["definition"].id
    assert call["trigger_source"] == "schedule"

    expected_occurrence = datetime(2026, 6, 1, 1, 0, 0, tzinfo=UTC)
    expected_key = build_idempotency_key(
        kind="schedule", entity_id=ctx["schedule"].id, occurrence=expected_occurrence
    )
    assert call["idempotency_key"] == expected_key


def test_tick_skips_a_cancelled_occurrence() -> None:
    now = datetime(2026, 6, 1, 1, 0, 5, tzinfo=UTC)
    service, ctx = _service()
    occurrence = datetime(2026, 6, 1, 1, 0, 0, tzinfo=UTC)

    ctx["schedules_repo"].list_skips_in_range.return_value = [
        ScheduleSkip(
            id=uuid4(),
            schedule_id=ctx["schedule"].id,
            occurrence=occurrence,
            created_at=now,
            restored_at=None,
        )
    ]

    result = service.tick(now=now)

    assert result == {"enqueued": 0}
    ctx["run_service"].start_run.assert_not_called()


def test_tick_does_not_skip_a_restored_occurrence() -> None:
    now = datetime(2026, 6, 1, 1, 0, 5, tzinfo=UTC)
    service, ctx = _service()
    occurrence = datetime(2026, 6, 1, 1, 0, 0, tzinfo=UTC)

    ctx["schedules_repo"].list_skips_in_range.return_value = [
        ScheduleSkip(
            id=uuid4(),
            schedule_id=ctx["schedule"].id,
            occurrence=occurrence,
            created_at=now,
            restored_at=now,  # undone
        )
    ]

    result = service.tick(now=now)

    assert result == {"enqueued": 1}


def test_tick_fires_a_due_extra_run_and_marks_it_fired() -> None:
    now = datetime(2026, 6, 1, 12, 0, 0, tzinfo=UTC)
    application_id = uuid4()
    extra = ScheduleExtraRun(
        id=uuid4(),
        application_id=application_id,
        run_at=datetime(2026, 6, 1, 11, 55, 0, tzinfo=UTC),
        created_at=now,
        fired_at=None,
    )

    schedules_repo = MagicMock()
    schedules_repo.list_active.return_value = []
    schedules_repo.list_skips_in_range.return_value = []
    schedules_repo.list_due_extra_runs.return_value = [extra]

    definition = _make_definition(application_id)
    definitions_repo = MagicMock()
    definitions_repo.find_main_for_application.return_value = definition

    run_service = MagicMock()
    run_service.was_already_created.return_value = False

    service = ScheduleService(
        schedule_repository=schedules_repo,
        definition_repository=definitions_repo,
        application_repository=MagicMock(),
        run_service=run_service,
    )

    result = service.tick(now=now)

    assert result == {"enqueued": 1}
    run_service.start_run.assert_called_once()
    schedules_repo.mark_extra_run_fired.assert_called_once_with(extra.id)

    expected_key = build_idempotency_key(kind="extra", entity_id=extra.id, occurrence=extra.run_at)
    assert run_service.start_run.call_args.kwargs["idempotency_key"] == expected_key


def test_tick_does_not_recount_an_occurrence_already_fired_by_an_earlier_tick() -> None:
    """A repeat call within the lookback window must still call start_run
    (idempotent, harmless) but must not report it as newly enqueued."""
    now = datetime(2026, 6, 1, 1, 0, 5, tzinfo=UTC)
    service, ctx = _service()
    ctx["run_service"].was_already_created.return_value = True

    result = service.tick(now=now)

    assert result == {"enqueued": 0}
    ctx["run_service"].start_run.assert_called_once()  # still called, just not counted


def test_tick_skips_a_schedule_whose_application_has_no_active_main_test() -> None:
    now = datetime(2026, 6, 1, 1, 0, 5, tzinfo=UTC)
    service, ctx = _service()
    ctx_definitions_repo = service._definitions  # noqa: SLF001 - test-only introspection
    ctx_definitions_repo.find_main_for_application.return_value = None

    result = service.tick(now=now)

    assert result == {"enqueued": 0}
    ctx["run_service"].start_run.assert_not_called()


class TestUpdateFrequency:
    """`update_frequency` must pivot on whatever occurrence is already next,
    never rewrite it, and stay correct across repeated edits."""

    def _schedule(self, **overrides) -> Schedule:
        return Schedule(
            id=uuid4(),
            application_id=uuid4(),
            every_hours=2,
            anchor_minute=0,
            timezone="Asia/Jerusalem",
            is_active=True,
            application_name="מגן עליון",
            **overrides,
        )

    def _service(self, schedule: Schedule) -> tuple[ScheduleService, MagicMock]:
        schedules_repo = MagicMock()
        schedules_repo.find_by_id.return_value = schedule
        schedules_repo.update_frequency.side_effect = (
            lambda schedule_id, *, every_hours, pending_every_hours, pending_effective_after: replace(
                schedule,
                every_hours=every_hours,
                pending_every_hours=pending_every_hours,
                pending_effective_after=pending_effective_after,
            )
        )
        service = ScheduleService(
            schedule_repository=schedules_repo,
            definition_repository=MagicMock(),
            application_repository=MagicMock(),
            run_service=MagicMock(),
        )
        return service, schedules_repo

    def test_pivots_on_the_next_occurrence_under_the_current_cadence(self) -> None:
        # 20:30 Asia/Jerusalem, mirroring the worked example: already ran at
        # 20:00, next due at 22:00.
        now = datetime(2026, 6, 1, 17, 30, 0, tzinfo=UTC)
        schedule = self._schedule()
        service, schedules_repo = self._service(schedule)

        updated = service.update_frequency(schedule.id, every_hours=1, now=now)

        expected_pivot = datetime(2026, 6, 1, 19, 0, 0, tzinfo=UTC)  # 22:00 local
        schedules_repo.update_frequency.assert_called_once_with(
            schedule.id,
            every_hours=2,  # the original cadence — its pivot has not fired yet
            pending_every_hours=1,
            pending_effective_after=expected_pivot,
        )
        assert updated.pending_every_hours == 1
        assert updated.pending_effective_after == expected_pivot
        # The old cadence's own next occurrence is exactly the pivot — it is
        # not skipped, moved, or duplicated.

    def test_editing_again_before_the_pivot_fires_keeps_the_same_pivot(self) -> None:
        """A second edit, made before the first pivot has happened, is still
        judged against the untouched base cadence — so it lands on the same
        pivot, just aimed at a different target frequency."""
        now = datetime(2026, 6, 1, 17, 30, 0, tzinfo=UTC)  # 20:30 local
        first_pivot = datetime(2026, 6, 1, 19, 0, 0, tzinfo=UTC)  # 22:00 local
        schedule = self._schedule(pending_every_hours=1, pending_effective_after=first_pivot)
        service, schedules_repo = self._service(schedule)

        service.update_frequency(schedule.id, every_hours=6, now=now)

        schedules_repo.update_frequency.assert_called_once_with(
            schedule.id,
            every_hours=2,  # the base cadence — the first pending change never went live
            pending_every_hours=6,
            pending_effective_after=first_pivot,
        )

    def test_editing_again_after_the_pivot_fired_pivots_on_the_new_cadence(self) -> None:
        """Once the first pivot is in the past, the schedule is already
        running on its (formerly pending) cadence — a further edit must
        pivot against *that*, not the original base cadence."""
        first_pivot = datetime(2026, 6, 1, 19, 0, 0, tzinfo=UTC)  # 22:00 local
        # Now sits after the first pivot, on the 3-hour cadence it introduced.
        now = datetime(2026, 6, 1, 20, 0, 0, tzinfo=UTC)  # 23:00 local — 1h after the first pivot
        schedule = self._schedule(pending_every_hours=3, pending_effective_after=first_pivot)
        service, schedules_repo = self._service(schedule)

        service.update_frequency(schedule.id, every_hours=1, now=now)

        # Next occurrence of the (pending-turned-live) 3-hour cadence after
        # 23:00 local, counting from the 22:00 pivot, is 01:00 local next day.
        expected_pivot = datetime(2026, 6, 1, 22, 0, 0, tzinfo=UTC)
        schedules_repo.update_frequency.assert_called_once_with(
            schedule.id,
            every_hours=3,  # the formerly-pending cadence, now live, gets committed
            pending_every_hours=1,
            pending_effective_after=expected_pivot,
        )

    def test_raises_not_found_for_an_unknown_schedule(self) -> None:
        schedules_repo = MagicMock()
        schedules_repo.find_by_id.return_value = None
        service = ScheduleService(
            schedule_repository=schedules_repo,
            definition_repository=MagicMock(),
            application_repository=MagicMock(),
            run_service=MagicMock(),
        )

        with pytest.raises(NotFoundError):
            service.update_frequency(uuid4(), every_hours=1)
