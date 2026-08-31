"""Schedule, skip and extra-run persistence."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from database import queries
from database.models import Schedule, ScheduleExtraRun, ScheduleSkip
from repositories.base_repository import BaseRepository


class ScheduleRepository(BaseRepository):
    """Reads and writes recurring schedules, their skips, and one-off extra runs."""

    # -- schedules ------------------------------------------------------
    def list_active(self) -> list[Schedule]:
        """List every active recurring schedule.

        Returns:
            Schedules with their application name joined, ordered the same
            way applications are ordered elsewhere in the interface.
        """
        rows = self.fetch_all(queries.SELECT_ACTIVE_SCHEDULES)
        return self.map_all(rows, Schedule.from_row)

    def find_by_id(self, schedule_id: UUID) -> Schedule | None:
        """Load one schedule by primary key.

        Args:
            schedule_id: The schedule's identifier.

        Returns:
            The schedule, or None if no such row exists.
        """
        row = self.fetch_one(queries.SELECT_SCHEDULE_BY_ID, {"schedule_id": str(schedule_id)})
        return self.map_one(row, Schedule.from_row)

    # -- skips ------------------------------------------------------------
    def list_skips_in_range(
        self, schedule_ids: list[UUID], *, start: datetime, end: datetime
    ) -> list[ScheduleSkip]:
        """List every skip touching a set of schedules within a range.

        Includes restored skips, not just active ones, so a caller can render
        a cancelled-then-undone occurrence correctly rather than it simply
        reappearing with no trace.

        Args:
            schedule_ids: Schedules to check. An empty list returns nothing.
            start: Range start, inclusive.
            end: Range end, exclusive.

        Returns:
            The matching skips.
        """
        if not schedule_ids:
            return []
        rows = self.fetch_all(
            queries.SELECT_SKIPS_IN_RANGE,
            {
                "schedule_ids": [str(schedule_id) for schedule_id in schedule_ids],
                "start": start,
                "end": end,
            },
        )
        return self.map_all(rows, ScheduleSkip.from_row)

    def skip(self, schedule_id: UUID, occurrence: datetime) -> ScheduleSkip:
        """Cancel one occurrence.

        Re-skipping an occurrence that was previously restored clears the
        restoration rather than erroring, since the caller's intent — "this
        should not run" — is the same either way.

        Args:
            schedule_id: The schedule the occurrence belongs to.
            occurrence: The UTC instant to cancel.

        Returns:
            The skip record.
        """
        row = self.execute_returning(
            queries.UPSERT_SCHEDULE_SKIP,
            {"schedule_id": str(schedule_id), "occurrence": occurrence},
        )
        assert row is not None, "UPSERT_SCHEDULE_SKIP always returns a row"
        return ScheduleSkip.from_row(row)

    def restore(self, schedule_id: UUID, occurrence: datetime) -> ScheduleSkip | None:
        """Undo a skip.

        Args:
            schedule_id: The schedule the occurrence belongs to.
            occurrence: The UTC instant to restore.

        Returns:
            The restored skip, or None if the occurrence was never skipped or
            was already restored.
        """
        row = self.execute_returning(
            queries.RESTORE_SCHEDULE_SKIP,
            {"schedule_id": str(schedule_id), "occurrence": occurrence},
        )
        return self.map_one(row, ScheduleSkip.from_row)

    # -- extra runs ---------------------------------------------------------
    def list_extra_runs_in_range(
        self, *, start: datetime, end: datetime
    ) -> list[ScheduleExtraRun]:
        """List one-off extra runs due within a range, fired or not.

        Args:
            start: Range start, inclusive.
            end: Range end, exclusive.

        Returns:
            The matching extra runs, ordered by when they are due.
        """
        rows = self.fetch_all(queries.SELECT_EXTRA_RUNS_IN_RANGE, {"start": start, "end": end})
        return self.map_all(rows, ScheduleExtraRun.from_row)

    def list_due_extra_runs(self, now: datetime) -> list[ScheduleExtraRun]:
        """List unfired extra runs whose time has arrived.

        Args:
            now: The instant to evaluate against.

        Returns:
            The extra runs a tick should enqueue.
        """
        rows = self.fetch_all(queries.SELECT_DUE_EXTRA_RUNS, {"now": now})
        return self.map_all(rows, ScheduleExtraRun.from_row)

    def create_extra_run(self, *, application_id: UUID, run_at: datetime) -> ScheduleExtraRun:
        """Create a one-off scheduled run.

        Does not touch the application's recurring schedule.

        Args:
            application_id: The application to run.
            run_at: The UTC instant it is scheduled for.

        Returns:
            The created extra run.
        """
        row = self.execute_returning(
            queries.INSERT_EXTRA_RUN,
            {"application_id": str(application_id), "run_at": run_at},
        )
        assert row is not None, "INSERT_EXTRA_RUN always returns a row"
        return ScheduleExtraRun.from_row(row)

    def mark_extra_run_fired(self, extra_run_id: UUID) -> ScheduleExtraRun | None:
        """Mark an extra run enqueued.

        Args:
            extra_run_id: The extra run to mark.

        Returns:
            The updated extra run, or None if it was already fired — meaning
            a concurrent tick won the race. Harmless either way, since the
            actual double-fire protection is the run's idempotency key; this
            just keeps this table's own bookkeeping honest.
        """
        row = self.execute_returning(
            queries.MARK_EXTRA_RUN_FIRED, {"extra_run_id": str(extra_run_id)}
        )
        return self.map_one(row, ScheduleExtraRun.from_row)

    def delete_pending_extra_run(self, extra_run_id: UUID) -> bool:
        """Remove a one-off run before it fires.

        Args:
            extra_run_id: The extra run to remove.

        Returns:
            True if a pending row was deleted. False if it did not exist, or
            had already fired — a run that already happened cannot be
            un-scheduled.
        """
        return (
            self.execute(queries.DELETE_PENDING_EXTRA_RUN, {"extra_run_id": str(extra_run_id)})
            > 0
        )
