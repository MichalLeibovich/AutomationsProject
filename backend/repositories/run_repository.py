"""Test run persistence.

Holds the idempotent insert, the run status state machine, the paged read used
by the timeline, and the partition maintenance helpers.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from typing import Any, Iterator
from uuid import UUID

from database import queries
from database.connection import server_side_cursor, transaction
from database.models import Page, TestDefinition, TestRun
from repositories.base_repository import BaseRepository
from utils.constants import GENERAL_SCOPE_LABEL, SCOPE_APPLICATION
from utils.logger import get_logger

logger = get_logger(__name__)


class RunRepository(BaseRepository):
    """Reads and writes runs on the monthly-partitioned runs table."""

    # -- reads --------------------------------------------------------------
    def list_paged(
        self,
        *,
        scope: str | None,
        status: str | None,
        trigger_source: str | None = None,
        search: str | None,
        date_from: datetime | None,
        date_to: datetime | None,
        sort: str,
        direction: str,
        limit: int,
        offset: int,
    ) -> Page:
        """Read a page of runs together with the total match count.

        Args:
            scope: None for all applications, ``"general"``, or an application
                name.
            status: Status to filter on; None or ``"all"`` disables the filter.
            trigger_source: Trigger source to filter on; None disables the
                filter — used by the history view's scheduled-only toggle.
            search: Full-text search term, or None.
            date_from: Earliest start time, inclusive, or None.
            date_to: Latest start time, inclusive, or None.
            sort: Sort key, resolved through a whitelist.
            direction: ``"asc"`` or ``"desc"``.
            limit: Page size.
            offset: Rows to skip.

        Returns:
            A page whose items are :class:`~database.models.TestRun` objects and
            whose total ignores pagination, so the interface can show how many
            rows remain.

        Raises:
            KeyError: If sort or direction is outside its whitelist.
        """
        params: dict[str, Any] = {
            "scope": scope,
            "status": None if status in (None, "all") else status,
            "trigger_source": trigger_source,
            "search": search or None,
            "date_from": date_from,
            "date_to": date_to,
            "limit": limit,
            "offset": offset,
        }

        rows = self.fetch_all(queries.build_run_list_query(sort, direction), params)
        total = self.fetch_scalar(queries.COUNT_RUNS, params, column="total", default=0)

        return Page(
            items=self.map_all(rows, TestRun.from_row),
            total=int(total or 0),
            limit=limit,
            offset=offset,
        )

    def find_by_id(self, run_id: UUID) -> TestRun | None:
        """Load one run by primary key.

        Args:
            run_id: The run's identifier.

        Returns:
            The run, or None if no such row exists.
        """
        row = self.fetch_one(queries.SELECT_RUN_BY_ID, {"run_id": str(run_id)})
        return self.map_one(row, TestRun.from_row)

    def list_active(
        self, limit: int = 200, settle_window: str = "30 seconds"
    ) -> list[dict[str, Any]]:
        """List runs for the live status stream.

        Returns everything in flight plus anything that finished within
        ``settle_window``. The second part matters: a run that reaches a terminal
        status stops being "active", so without it the run would disappear from
        the feed and every client would be left showing "running" indefinitely.

        The projection is deliberately narrow, because this is polled repeatedly
        for as long as any dashboard is open.

        Args:
            limit: Maximum runs to return.
            settle_window: How long a finished run keeps being broadcast. Long
                enough that a client which just reconnected still sees the
                transition, short enough not to replay old history.

        Returns:
            Rows containing only the columns the stream needs.
        """
        return self.fetch_all(
            queries.SELECT_ACTIVE_RUNS, {"limit": limit, "settle_window": settle_window}
        )

    def find_by_idempotency_key(self, idempotency_key: str) -> TestRun | None:
        """Load the run previously created for an idempotency key, if any.

        Used only to tell an already-fired scheduled occurrence apart from a
        newly-fired one for logging purposes — the actual double-fire
        guarantee comes from the unique constraint :meth:`create` claims
        against, not from this check.

        Args:
            idempotency_key: The key to look up.

        Returns:
            The run, or None if no claim exists for this key yet.
        """
        row = self.fetch_one(
            queries.SELECT_RUN_BY_IDEMPOTENCY_KEY, {"idempotency_key": idempotency_key}
        )
        return self.map_one(row, TestRun.from_row)

    def list_recent_scheduled(self, limit: int) -> list[TestRun]:
        """List the most recent scheduler-originated runs.

        Covers both recurring occurrences and one-off extra runs — both are
        recorded with ``trigger_source='schedule'``; only the run's
        ``idempotency_key`` prefix tells them apart (see
        :mod:`utils.schedule_time`).

        Args:
            limit: Maximum runs to return.

        Returns:
            The runs, most recently started first.
        """
        rows = self.fetch_all(queries.SELECT_RECENT_SCHEDULED_RUNS, {"limit": limit})
        return self.map_all(rows, TestRun.from_row)

    def iter_for_export(
        self,
        *,
        scope: str | None,
        status: str | None,
        trigger_source: str | None = None,
        search: str | None,
    ) -> Iterator[dict[str, Any]]:
        """Stream every matching run for CSV export.

        Rows come through a server-side cursor, so a large export never
        materialises in memory.

        Args:
            scope: Scope filter, as in :meth:`list_paged`.
            status: Status filter; None or ``"all"`` disables it.
            trigger_source: Trigger source filter; None disables it.
            search: Full-text search term, or None.

        Yields:
            One row per matching run, most recent first.
        """
        params = {
            "scope": scope,
            "status": None if status in (None, "all") else status,
            "trigger_source": trigger_source,
            "search": search or None,
            "date_from": None,
            "date_to": None,
        }

        with server_side_cursor("run_export") as cursor:
            cursor.execute(queries.build_export_query(), params)
            for row in cursor:
                yield dict(row)

    # -- writes -------------------------------------------------------------
    def create(
        self,
        *,
        definition: TestDefinition,
        triggered_by: str,
        trigger_source: str,
        idempotency_key: str,
        correlation_id: str | None = None,
    ) -> TestRun:
        """Enqueue a run idempotently.

        The idempotency claim is taken in an unpartitioned table, which is what
        makes the guarantee real. A unique index on the runs table could not
        enforce it: a partitioned table's unique index must include the partition
        key ``started_at``, which differs between retries, so two submissions
        would never collide and the same automation could fire twice.

        The claim and the insert share one transaction, so a crash between them
        cannot leave a key reserved for a run that does not exist.

        Args:
            definition: The automation being run. Its scope and application
                determine the frozen scope label.
            triggered_by: Free text recorded on the run — a hostname, a CI job
                name, or ``"manual"``.
            trigger_source: One of manual, bulk, schedule, ci or api.
            idempotency_key: Caller-generated key; a repeat returns the original
                run.
            correlation_id: Request correlation identifier, or None.

        Returns:
            The newly created run, or the run previously created for this key.

        Raises:
            psycopg2.Error: If the transaction fails.
        """
        run_id = uuid.uuid4()
        started_at = datetime.now(UTC)

        scope_label = (
            definition.application_name
            if definition.scope == SCOPE_APPLICATION
            else GENERAL_SCOPE_LABEL
        )

        with transaction() as cursor:
            cursor.execute(queries.ENSURE_PARTITION_FOR_TODAY)

            cursor.execute(
                queries.CLAIM_IDEMPOTENCY_KEY,
                {
                    "idempotency_key": idempotency_key,
                    "run_id": str(run_id),
                    "run_started_at": started_at,
                },
            )

            if cursor.fetchone() is None:
                cursor.execute(
                    queries.SELECT_RUN_BY_IDEMPOTENCY_KEY,
                    {"idempotency_key": idempotency_key},
                )
                existing = cursor.fetchone()
                if existing is not None:
                    logger.info("idempotent replay", extra={"idempotency_key": idempotency_key})
                    return TestRun.from_row(dict(existing))

            cursor.execute(
                queries.INSERT_RUN,
                {
                    "run_id": str(run_id),
                    "definition_id": str(definition.id),
                    "application_id": (
                        str(definition.application_id) if definition.application_id else None
                    ),
                    "scope": definition.scope,
                    "scope_label": scope_label,
                    "test_name": definition.name,
                    "runner_target": definition.runner_target,
                    "started_at": started_at,
                    "triggered_by": triggered_by,
                    "trigger_source": trigger_source,
                    "idempotency_key": idempotency_key,
                    "correlation_id": correlation_id,
                },
            )
            row = cursor.fetchone()

        assert row is not None, "INSERT_RUN always returns a row"
        logger.info(
            "run enqueued", extra={"run_id": str(run_id), "target": definition.runner_target}
        )
        return TestRun.from_row(dict(row))

    def mark_running(self, run_id: UUID, worker_id: str) -> TestRun | None:
        """Claim a queued run for a worker.

        The status guard makes the claim atomic, so two workers cannot both take
        the same run.

        Args:
            run_id: The run to claim.
            worker_id: Identifier of the claiming worker.

        Returns:
            The updated run, or None if it was not queued.
        """
        row = self.execute_returning(
            queries.MARK_RUN_RUNNING, {"run_id": str(run_id), "worker_id": worker_id}
        )
        return self.map_one(row, TestRun.from_row)

    def complete(
        self,
        run_id: UUID,
        *,
        status: str,
        failure_feature: str | None = None,
        failure_error_type: str | None = None,
        failure_reason: str | None = None,
        stack_trace: str | None = None,
    ) -> TestRun | None:
        """Transition an in-flight run to a terminal status.

        Args:
            run_id: The run to complete.
            status: Terminal status to record.
            failure_feature: Failing component, for the failure breakdown.
            failure_error_type: Failure category, for the error-type breakdown.
            failure_reason: Human-readable explanation for the debrief.
            stack_trace: Full traceback, when the runner captured one.

        Returns:
            The updated run, or None if it had already finished.
        """
        row = self.execute_returning(
            queries.COMPLETE_RUN,
            {
                "run_id": str(run_id),
                "status": status,
                "failure_feature": failure_feature,
                "failure_error_type": failure_error_type,
                "failure_reason": failure_reason,
                "stack_trace": stack_trace,
            },
        )
        return self.map_one(row, TestRun.from_row)

    def cancel(self, run_id: UUID, actor_name: str) -> TestRun | None:
        """Cancel an in-flight run.

        Args:
            run_id: The run to cancel.
            actor_name: Name recorded in the cancellation reason.

        Returns:
            The cancelled run, or None if it had already finished.
        """
        row = self.execute_returning(
            queries.CANCEL_RUN,
            {"run_id": str(run_id), "reason": f"הופסקה על ידי {actor_name} לפני שהסתיימה."},
        )
        return self.map_one(row, TestRun.from_row)

    # -- maintenance --------------------------------------------------------
    def ensure_partitions(self, months_ahead: int = 3) -> list[str]:
        """Pre-create run partitions for the coming months.

        Args:
            months_ahead: How many months beyond the current one to provision.

        Returns:
            The partition names that now exist.
        """
        names: list[str] = []
        with transaction() as cursor:
            for offset in range(months_ahead + 1):
                cursor.execute(queries.ENSURE_PARTITION_AT_OFFSET, {"offset_months": offset})
                row = cursor.fetchone()
                if row:
                    names.append(row["partition_name"])
        return names

    def drop_partitions_before(self, cutoff: date) -> int:
        """Drop run partitions wholly older than a cutoff.

        Retention is a metadata operation rather than a mass row delete, which
        keeps it fast as history grows.

        Args:
            cutoff: Partitions ending at or before this date are dropped.

        Returns:
            The number of partitions dropped.
        """
        row = self.execute_returning(queries.DROP_PARTITIONS_BEFORE, {"cutoff": cutoff})
        return int(row["dropped"]) if row else 0

    def prune_idempotency_claims(self) -> int:
        """Delete idempotency claims past their retention interval.

        Returns:
            The number of claims removed.
        """
        row = self.execute_returning(queries.PRUNE_IDEMPOTENCY_CLAIMS)
        return int(row["removed"]) if row else 0
