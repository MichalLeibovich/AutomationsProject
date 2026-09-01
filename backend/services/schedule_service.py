"""Scheduled-automation orchestration.

Owns the rule the interface only hints at: occurrences are never stored, only
computed on demand from each schedule's cadence (see
:mod:`utils.schedule_time`), and a run's association with the occurrence that
produced it lives entirely in its idempotency key — no ``scheduled_for``
column on ``test_runs``.

:meth:`ScheduleService.tick` is the one entry point the worker calls; every
other method serves the interface: what is coming up, what recently ran,
skipping or restoring a recurring occurrence, and adding or removing a
one-off extra run.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import UUID

from database.models import (
    Schedule,
    ScheduledOccurrence,
    ScheduledRunEntry,
    ScheduledRunGroup,
    ScheduleExtraRun,
)
from repositories.application_repository import ApplicationRepository
from repositories.schedule_repository import ScheduleRepository
from repositories.test_definition_repository import TestDefinitionRepository
from services.run_service import RunService
from utils import schedule_time
from utils.constants import TRIGGER_SCHEDULE
from utils.errors import NotFoundError, ValidationError
from utils.logger import get_logger

logger = get_logger(__name__)

TICK_TRIGGERED_BY = "מתזמן"
"""Recorded as `triggered_by` on every run the scheduler creates."""

TICK_LOOKBACK = timedelta(minutes=10)
"""How far back a tick looks for recurring occurrences it has not yet fired.

Comfortably larger than the worker's tick interval, so an occasionally slow
or delayed tick never misses a slot. Deliberately not large enough to
back-fill hours of missed occurrences after a real outage — a worker down
overnight should not come back and fire a dozen queued slots at once. A
one-off extra run has no such limit, since firing a single late run late
carries none of that flooding risk.
"""

RECENT_FETCH_MULTIPLIER = 6
"""How many raw runs to fetch per requested group in :meth:`list_recent`.

Several applications' runs collapse into one occurrence group, so fetching
only ``limit`` raw runs would usually return far fewer than ``limit`` groups.
"""


class ScheduleService:
    """Computes upcoming/recent scheduled automation and fires due ones."""

    def __init__(
        self,
        schedule_repository: ScheduleRepository | None = None,
        definition_repository: TestDefinitionRepository | None = None,
        application_repository: ApplicationRepository | None = None,
        run_service: RunService | None = None,
    ) -> None:
        """Initialise the service.

        Args:
            schedule_repository: Schedule, skip and extra-run persistence.
                Defaults to a real repository.
            definition_repository: Automation catalog lookups. Defaults to a
                real repository.
            application_repository: Application lookups, for validating an
                extra run's target. Defaults to a real repository.
            run_service: Run triggering. Reused rather than writing to
                ``test_runs`` directly, so a scheduled run is subject to the
                same rules — active-definition check, idempotent creation —
                as every other trigger path. Defaults to a real service.
        """
        self._schedules = schedule_repository or ScheduleRepository()
        self._definitions = definition_repository or TestDefinitionRepository()
        self._applications = application_repository or ApplicationRepository()
        self._runs = run_service or RunService()

    # -- reads ----------------------------------------------------------
    def list_schedules(self) -> list[Schedule]:
        """List every active recurring schedule.

        Returns:
            The schedules, application name joined.
        """
        return self._schedules.list_active()

    def list_upcoming(self, *, hours: int = 24) -> list[ScheduledOccurrence]:
        """List every occurrence due in the next ``hours``.

        Includes skipped occurrences — cancelled but still listed, greyed out
        by the interface with a restore action, so a deliberate gap does not
        look like a bug.

        Args:
            hours: How far ahead to look.

        Returns:
            Occurrences in ascending order, recurring and one-off mixed.
        """
        now = datetime.now(UTC)
        end = now + timedelta(hours=hours)
        schedules = self.list_schedules()

        active_skips = {
            (skip.schedule_id, skip.occurrence)
            for skip in self._schedules.list_skips_in_range(
                [schedule.id for schedule in schedules], start=now, end=end
            )
            if skip.is_active
        }

        results: list[ScheduledOccurrence] = []

        for schedule in schedules:
            occurrences = schedule_time.occurrences_between(
                every_hours=schedule.every_hours,
                anchor_minute=schedule.anchor_minute,
                timezone=schedule.timezone,
                start_utc=now,
                end_utc=end,
                pending_every_hours=schedule.pending_every_hours,
                pending_effective_after=schedule.pending_effective_after,
            )
            for occurrence in occurrences:
                results.append(
                    ScheduledOccurrence(
                        kind="schedule",
                        occurrence=occurrence,
                        application_id=schedule.application_id,
                        application_name=schedule.application_name or "",
                        schedule_id=schedule.id,
                        skipped=(schedule.id, occurrence) in active_skips,
                    )
                )

        for extra in self._schedules.list_extra_runs_in_range(start=now, end=end):
            if extra.fired_at is not None:
                continue
            results.append(
                ScheduledOccurrence(
                    kind="extra",
                    occurrence=extra.run_at,
                    application_id=extra.application_id,
                    application_name=extra.application_name or "",
                    extra_run_id=extra.id,
                    skipped=False,
                )
            )

        results.sort(key=lambda item: item.occurrence)
        return results

    def list_recent(self, *, limit: int = 8) -> list[ScheduledRunGroup]:
        """List the most recent scheduled occurrences that actually ran.

        Runs sharing one occurrence — for example Magen Elyon and Harmony,
        both on a two-hour cadence — land under one group even though their
        ``started_at`` values differ by however many seconds separated their
        individual inserts, because grouping keys on the occurrence encoded
        in each run's idempotency key rather than on ``started_at`` itself.

        Args:
            limit: Maximum groups to return.

        Returns:
            Groups in descending order, most recent first.
        """
        raw_runs = self._runs.list_recent_scheduled(limit=limit * RECENT_FETCH_MULTIPLIER)

        grouped: dict[datetime, list[ScheduledRunEntry]] = {}
        for run in raw_runs:
            origin = schedule_time.parse_idempotency_key(run.idempotency_key)
            occurrence = origin.occurrence if origin is not None else run.started_at

            if run.application_id is None:
                continue  # a scheduled run always targets an application; a
                # general-scope row here would indicate a bug elsewhere.

            grouped.setdefault(occurrence, []).append(
                ScheduledRunEntry(
                    application_id=run.application_id,
                    application_name=run.scope_label,
                    run_id=run.id,
                    status=run.status,
                )
            )

        ordered = sorted(grouped.keys(), reverse=True)[:limit]
        return [ScheduledRunGroup(occurrence=occurrence, entries=grouped[occurrence]) for occurrence in ordered]

    # -- frequency ----------------------------------------------------------
    def update_frequency(
        self, schedule_id: UUID, *, every_hours: int, now: datetime | None = None
    ) -> Schedule:
        """Change a schedule's cadence, without touching its committed next run.

        The new cadence never applies retroactively: whichever occurrence is
        already next right now — under whatever cadence currently governs,
        possibly itself a still-pending change from an earlier edit — keeps
        being produced as-is, and `every_hours` only starts counting
        occurrences after that instant. See
        :func:`utils.schedule_time.occurrences_between` for the mechanics
        this relies on.

        Args:
            schedule_id: The schedule to update.
            every_hours: The new interval between occurrences, in hours.
            now: The instant to pivot against. Defaults to the current time;
                overridable for tests.

        Returns:
            The updated schedule.

        Raises:
            NotFoundError: If no such schedule exists.
            ValidationError: If no occurrence to pivot on was found — should
                not happen in practice, since every valid cadence fires at
                least once a day.
        """
        schedule = self._get_schedule(schedule_id)
        now = now or datetime.now(UTC)

        pivot = schedule_time.next_occurrence(
            every_hours=schedule.every_hours,
            anchor_minute=schedule.anchor_minute,
            timezone=schedule.timezone,
            after_utc=now,
            horizon_hours=48,
            pending_every_hours=schedule.pending_every_hours,
            pending_effective_after=schedule.pending_effective_after,
        )
        if pivot is None:
            raise ValidationError(
                details={"everyHours": ["לא נמצאה ריצה עתידית לתזמן את השינוי אחריה"]}
            )

        # `occurrences_between` only ever composes one committed cadence with
        # one pending one. If an earlier pending change has already taken
        # over (its pivot is behind us), that cadence — not the original
        # `every_hours` — is what is actually live right now, and it is what
        # must be committed here: otherwise it is lost the moment this edit
        # overwrites the pending pair, and every read between now and the new
        # pivot would silently fall back to the stale original cadence.
        current_every_hours = (
            schedule.pending_every_hours
            if schedule.pending_effective_after is not None and schedule.pending_effective_after <= now
            else schedule.every_hours
        )

        updated = self._schedules.update_frequency(
            schedule_id,
            every_hours=current_every_hours,
            pending_every_hours=every_hours,
            pending_effective_after=pivot,
        )
        assert updated is not None, "schedule existed a moment ago"

        logger.info(
            "schedule frequency changed",
            extra={
                "schedule_id": str(schedule_id),
                "every_hours": every_hours,
                "effective_after": pivot.isoformat(),
            },
        )
        return updated

    # -- skip / restore ---------------------------------------------------
    def skip(self, schedule_id: UUID, occurrence: datetime) -> None:
        """Cancel one occurrence of a recurring schedule.

        Args:
            schedule_id: The schedule the occurrence belongs to.
            occurrence: The UTC instant to cancel.

        Raises:
            NotFoundError: If no such schedule exists.
        """
        self._get_schedule(schedule_id)
        self._schedules.skip(schedule_id, occurrence)
        logger.info(
            "schedule occurrence skipped",
            extra={"schedule_id": str(schedule_id), "occurrence": occurrence.isoformat()},
        )

    def restore(self, schedule_id: UUID, occurrence: datetime) -> None:
        """Undo a skip.

        Args:
            schedule_id: The schedule the occurrence belongs to.
            occurrence: The UTC instant to restore.

        Raises:
            NotFoundError: If no such schedule exists, or the occurrence was
                never skipped, or was already restored.
        """
        self._get_schedule(schedule_id)
        if self._schedules.restore(schedule_id, occurrence) is None:
            raise NotFoundError("הריצה לא הייתה מבוטלת")

    # -- extra runs -------------------------------------------------------
    def add_extra(self, *, application_id: UUID, run_at: datetime) -> ScheduleExtraRun:
        """Schedule one one-off run.

        Does not touch the application's recurring schedule.

        Args:
            application_id: The application to run.
            run_at: The UTC instant to run it at. Must be in the future.

        Returns:
            The created extra run.

        Raises:
            NotFoundError: If no such application exists.
            ValidationError: If ``run_at`` is in the past.
        """
        application = self._applications.find_by_id(application_id)
        if application is None:
            raise NotFoundError("האפליקציה לא נמצאה")
        if run_at <= datetime.now(UTC):
            raise ValidationError(details={"runAt": ["לא ניתן לתזמן ריצה בעבר"]})

        created = self._schedules.create_extra_run(application_id=application_id, run_at=run_at)
        logger.info(
            "extra run scheduled",
            extra={"application_id": str(application_id), "run_at": run_at.isoformat()},
        )
        # The insert has nothing to join against, so the name comes from the
        # application already loaded to validate the request.
        return replace(created, application_name=application.name)

    def remove_extra(self, extra_run_id: UUID) -> None:
        """Remove a one-off run before it fires.

        Args:
            extra_run_id: The extra run to remove.

        Raises:
            NotFoundError: If it does not exist, or had already fired — a run
                that already happened cannot be un-scheduled.
        """
        if not self._schedules.delete_pending_extra_run(extra_run_id):
            raise NotFoundError("הריצה לא נמצאה או שכבר בוצעה")

    # -- worker entry point -------------------------------------------------
    def tick(self, now: datetime | None = None) -> dict[str, int]:
        """Enqueue every occurrence that has come due.

        Called by the worker on a timer, independent of its queue-draining
        loop. Safe to call from multiple worker replicas at once, and safe to
        call more often than strictly necessary: every enqueue goes through
        :meth:`RunService.start_run`, which claims an idempotency key derived
        deterministically from the schedule (or extra run) and the
        occurrence — a repeat, from this or any other replica, always
        resolves to the same run rather than creating a second one.

        Args:
            now: The instant to evaluate against. Defaults to the current
                time; overridable for tests.

        Returns:
            ``{"enqueued": n}``, the number of runs this call actually
            created — 0 on a call that found nothing newly due, which is the
            common case.
        """
        now = now or datetime.now(UTC)
        enqueued = 0

        enqueued += self._tick_schedules(now)
        enqueued += self._tick_extras(now)

        return {"enqueued": enqueued}

    def _tick_schedules(self, now: datetime) -> int:
        """Enqueue due occurrences of every active recurring schedule.

        Args:
            now: The instant to evaluate against.

        Returns:
            Runs created.
        """
        window_start = now - TICK_LOOKBACK
        window_end = now + timedelta(seconds=1)
        enqueued = 0

        schedules = self._schedules.list_active()
        active_skips = {
            (skip.schedule_id, skip.occurrence)
            for skip in self._schedules.list_skips_in_range(
                [schedule.id for schedule in schedules], start=window_start, end=window_end
            )
            if skip.is_active
        }

        for schedule in schedules:
            occurrences = schedule_time.occurrences_between(
                every_hours=schedule.every_hours,
                anchor_minute=schedule.anchor_minute,
                timezone=schedule.timezone,
                start_utc=window_start,
                end_utc=window_end,
                pending_every_hours=schedule.pending_every_hours,
                pending_effective_after=schedule.pending_effective_after,
            )
            if not occurrences:
                continue

            definition = self._definitions.find_main_for_application(schedule.application_id)
            if definition is None:
                logger.warning(
                    "schedule has no active main test",
                    extra={"schedule_id": str(schedule.id), "application_id": str(schedule.application_id)},
                )
                continue

            for occurrence in occurrences:
                if (schedule.id, occurrence) in active_skips:
                    continue

                key = schedule_time.build_idempotency_key(
                    kind="schedule", entity_id=schedule.id, occurrence=occurrence
                )
                # Checked ahead of creating, purely so a tick that lands
                # inside the lookback window's overlap with the previous one
                # does not report the same occurrence as newly enqueued
                # every time. The actual double-fire guarantee is the
                # database constraint start_run claims against regardless.
                already_fired = self._runs.was_already_created(key)
                self._runs.start_run(
                    definition_id=definition.id,
                    idempotency_key=key,
                    triggered_by=TICK_TRIGGERED_BY,
                    trigger_source=TRIGGER_SCHEDULE,
                )
                if not already_fired:
                    enqueued += 1

        return enqueued

    def _tick_extras(self, now: datetime) -> int:
        """Enqueue every unfired one-off run whose time has arrived.

        Args:
            now: The instant to evaluate against.

        Returns:
            Runs created.
        """
        enqueued = 0

        for extra in self._schedules.list_due_extra_runs(now):
            definition = self._definitions.find_main_for_application(extra.application_id)
            if definition is None:
                logger.warning(
                    "extra run has no active main test",
                    extra={"extra_run_id": str(extra.id), "application_id": str(extra.application_id)},
                )
                continue

            key = schedule_time.build_idempotency_key(
                kind="extra", entity_id=extra.id, occurrence=extra.run_at
            )
            already_fired = self._runs.was_already_created(key)
            self._runs.start_run(
                definition_id=definition.id,
                idempotency_key=key,
                triggered_by=TICK_TRIGGERED_BY,
                trigger_source=TRIGGER_SCHEDULE,
            )
            # Marked after the run is claimed, not before: if the process
            # dies in between, the next tick's `run_at <= now` check simply
            # finds it due again and re-fires it — which the idempotency key
            # turns into a no-op, not a duplicate.
            self._schedules.mark_extra_run_fired(extra.id)
            if not already_fired:
                enqueued += 1

        return enqueued

    # -- internal -----------------------------------------------------------
    def _get_schedule(self, schedule_id: UUID) -> Schedule:
        """Load one schedule, raising if it does not exist.

        Args:
            schedule_id: The schedule to load.

        Returns:
            The schedule.

        Raises:
            NotFoundError: If no such schedule exists.
        """
        schedule = self._schedules.find_by_id(schedule_id)
        if schedule is None:
            raise NotFoundError("התזמון לא נמצא")
        return schedule
