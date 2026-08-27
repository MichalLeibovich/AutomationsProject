"""Run orchestration.

Owns the rules the interface only hints at: that a bulk trigger never touches
general automation, that a failed run must carry a reason, and that a run can
only be completed once. Because the rules live here rather than in a route,
every caller — HTTP, scheduler, or the automation suite reporting its own
results — is subject to them.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any, Iterator
from uuid import UUID

from database.models import (
    Page,
    RunArtifact,
    RunComment,
    RunStep,
    TestRun,
)
from repositories.comment_repository import ArtifactRepository, CommentRepository
from repositories.run_repository import RunRepository
from repositories.step_repository import StepRepository
from repositories.test_definition_repository import TestDefinitionRepository
from utils.constants import SCOPE_GENERAL, TERMINAL_STATUSES, TRIGGER_BULK
from utils.errors import ConflictError, NotFoundError, ValidationError
from utils.logger import get_logger

logger = get_logger(__name__)


class RunService:
    """Triggers runs, records their outcome, and serves run detail."""

    def __init__(
        self,
        run_repository: RunRepository | None = None,
        definition_repository: TestDefinitionRepository | None = None,
        step_repository: StepRepository | None = None,
        artifact_repository: ArtifactRepository | None = None,
        comment_repository: CommentRepository | None = None,
    ) -> None:
        """Initialise the service.

        Args:
            run_repository: Run persistence. Defaults to a real repository.
            definition_repository: Automation lookups. Defaults to a real
                repository.
            step_repository: Step persistence. Defaults to a real repository.
            artifact_repository: Artifact metadata. Defaults to a real
                repository.
            comment_repository: Comment persistence. Defaults to a real
                repository.
        """
        self._runs = run_repository or RunRepository()
        self._definitions = definition_repository or TestDefinitionRepository()
        self._steps = step_repository or StepRepository()
        self._artifacts = artifact_repository or ArtifactRepository()
        self._comments = comment_repository or CommentRepository()

    # -- reads --------------------------------------------------------------
    def list_runs(self, **filters: Any) -> Page:
        """Read a page of runs.

        Args:
            **filters: Keyword arguments accepted by
                :meth:`RunRepository.list_paged`, normally produced by
                :func:`~utils.validators.validate_run_list_query`.

        Returns:
            A page of runs with the total match count.
        """
        return self._runs.list_paged(**filters)

    def get_run(self, run_id: UUID) -> TestRun:
        """Load one run.

        Args:
            run_id: The run to load.

        Returns:
            The run.

        Raises:
            NotFoundError: If no such run exists.
        """
        run = self._runs.find_by_id(run_id)
        if run is None:
            raise NotFoundError("הריצה לא נמצאה")
        return run

    def list_active_runs(self) -> list[dict[str, Any]]:
        """Build the live status payload.

        Covers runs in flight and runs that just finished. Broadcasting the
        finished ones briefly is what delivers the terminal frame: a run that
        simply stopped appearing would leave every client showing "running" with
        the clock still ticking.

        Elapsed seconds are computed server-side so every client shows the same
        value regardless of clock skew, and a backgrounded tab is correct the
        moment it returns. For a finished run the elapsed time is frozen at its
        real duration rather than continuing to grow.

        Returns:
            One camelCase mapping per run, ready to serialise into a server-sent
            event.
        """
        now = datetime.now(UTC)
        updates: list[dict[str, Any]] = []

        for row in self._runs.list_active():
            started = row["started_at"]
            ended = row.get("ended_at")

            # A finished run reports the time it actually took; an in-flight one
            # reports how long it has been going.
            elapsed = int(((ended or now) - started).total_seconds())

            updates.append(
                {
                    "runId": str(row["id"]),
                    "testDefinitionId": str(row["test_definition_id"]),
                    "status": row["status"],
                    "elapsedSeconds": max(0, elapsed),
                    "durationSeconds": row.get("duration_seconds"),
                    "failureReason": row.get("failure_reason"),
                }
            )
        return updates

    # -- triggering ---------------------------------------------------------
    def start_run(
        self,
        *,
        definition_id: UUID,
        idempotency_key: str,
        triggered_by: str = "manual",
        trigger_source: str = "manual",
        correlation_id: str | None = None,
    ) -> TestRun:
        """Enqueue a single automation run.

        Args:
            definition_id: The automation to run.
            idempotency_key: Caller-generated key. Repeating a key returns the
                original run rather than enqueueing a second, so a double-click
                or a retried request cannot double-fire.
            triggered_by: Free text recorded on the run.
            trigger_source: manual, bulk, schedule, ci or api.
            correlation_id: Request correlation identifier, or None.

        Returns:
            The queued run, or the existing run for a repeated key.

        Raises:
            NotFoundError: If the automation does not exist.
            ConflictError: If it is inactive.
        """
        definition = self._definitions.find_by_id(definition_id)
        if definition is None:
            raise NotFoundError("הבדיקה לא נמצאה")
        if not definition.is_active:
            raise ConflictError("הבדיקה אינה פעילה")

        return self._runs.create(
            definition=definition,
            triggered_by=triggered_by,
            trigger_source=trigger_source,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )

    def start_run_by_target(
        self,
        *,
        runner_target: str,
        idempotency_key: str,
        triggered_by: str = "automation",
        trigger_source: str = "ci",
        correlation_id: str | None = None,
    ) -> TestRun:
        """Enqueue a run identified by its pytest node id.

        This is the entry point the automation suite uses: it knows which test it
        is about to execute, but not any database identifier.

        Args:
            runner_target: The node id, such as
                ``tests/test_login.py::test_valid_login``.
            idempotency_key: Caller-generated key.
            triggered_by: Free text recorded on the run, typically a hostname.
            trigger_source: manual, bulk, schedule, ci or api.
            correlation_id: Request correlation identifier, or None.

        Returns:
            The queued run.

        Raises:
            NotFoundError: If the automation is not registered in the catalog.
            ConflictError: If it is inactive.
        """
        definition = self._definitions.find_by_runner_target(runner_target)
        if definition is None:
            raise NotFoundError(f"האוטומציה '{runner_target}' אינה רשומה במערכת")
        if not definition.is_active:
            raise ConflictError("הבדיקה אינה פעילה")

        return self._runs.create(
            definition=definition,
            triggered_by=triggered_by,
            trigger_source=trigger_source,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )

    def start_bulk_main(
        self,
        *,
        scope: str | None,
        idempotency_key: str,
        triggered_by: str = "manual",
        correlation_id: str | None = None,
    ) -> list[TestRun]:
        """Enqueue the main test of every application in scope.

        The general scope is refused outright rather than filtered out.
        Bulk-firing automation that changes production state is precisely the
        accident worth designing out, which is also why the interface hides the
        control there.

        Each run receives a key derived from ``idempotency_key``, so retrying the
        whole request replays the batch idempotently rather than partially.

        Args:
            scope: Application name to restrict to, or None for all.
            idempotency_key: Caller-generated key for the batch.
            triggered_by: Free text recorded on each run.
            correlation_id: Request correlation identifier, or None.

        Returns:
            The queued runs, one per matching application.

        Raises:
            ValidationError: If ``scope`` is the general scope.
        """
        if scope == SCOPE_GENERAL:
            raise ValidationError("לא ניתן להריץ הרצה קבוצתית בתחום הכללי")

        definitions = self._definitions.list_main_for_bulk(scope)
        started: list[TestRun] = []

        for index, definition in enumerate(definitions):
            started.append(
                self._runs.create(
                    definition=definition,
                    triggered_by=triggered_by,
                    trigger_source=TRIGGER_BULK,
                    idempotency_key=f"{idempotency_key}:{index}",
                    correlation_id=correlation_id,
                )
            )

        logger.info("bulk run started", extra={"count": len(started), "scope": scope})
        return started

    def cancel_run(self, run_id: UUID, actor_name: str = "מפעיל") -> TestRun:
        """Cancel an in-flight run.

        Args:
            run_id: The run to cancel.
            actor_name: Name recorded in the cancellation reason.

        Returns:
            The cancelled run.

        Raises:
            NotFoundError: If no such run exists.
            ConflictError: If it had already finished, including when it finishes
                between the read and the update.
        """
        run = self.get_run(run_id)
        if run.status in TERMINAL_STATUSES:
            raise ConflictError("הריצה כבר הסתיימה")

        cancelled = self._runs.cancel(run_id, actor_name)
        if cancelled is None:
            raise ConflictError("הריצה כבר הסתיימה")
        return cancelled

    # -- runner callbacks ---------------------------------------------------
    def claim_run(self, run_id: UUID, worker_id: str) -> TestRun:
        """Claim a queued run on behalf of a worker.

        Args:
            run_id: The run to claim.
            worker_id: Identifier of the claiming worker.

        Returns:
            The run, now marked running.

        Raises:
            ConflictError: If it was not queued, meaning another worker won the
                race or the run already finished.
        """
        claimed = self._runs.mark_running(run_id, worker_id)
        if claimed is None:
            raise ConflictError("הריצה אינה בתור")
        return claimed

    def complete_run(
        self,
        run_id: UUID,
        *,
        status: str,
        failure_feature: str | None = None,
        failure_error_type: str | None = None,
        failure_reason: str | None = None,
        stack_trace: str | None = None,
    ) -> TestRun:
        """Record the outcome of a run.

        Args:
            run_id: The run to complete.
            status: Terminal status to record.
            failure_feature: Failing component, for the failure breakdown.
            failure_error_type: Failure category, for the error-type breakdown.
            failure_reason: Human-readable explanation. Mandatory for a failure,
                because a debrief without one is unusable to the next shift.
            stack_trace: Full traceback, when the runner captured one.

        Returns:
            The completed run.

        Raises:
            ValidationError: If the status is not terminal, or a failure carries
                no reason.
            ConflictError: If the run had already finished.
        """
        if status not in TERMINAL_STATUSES:
            raise ValidationError("סטטוס סיום אינו תקין")
        if status == "failed" and not failure_reason:
            raise ValidationError("ריצה שנכשלה מחייבת תיאור כשל")

        completed = self._runs.complete(
            run_id,
            status=status,
            failure_feature=failure_feature,
            failure_error_type=failure_error_type,
            failure_reason=failure_reason,
            stack_trace=stack_trace,
        )
        if completed is None:
            raise ConflictError("הריצה כבר הסתיימה")

        logger.info("run completed", extra={"run_id": str(run_id), "status": status})
        return completed

    # -- steps --------------------------------------------------------------
    def list_steps(self, run_id: UUID) -> list[RunStep]:
        """List a run's steps.

        Args:
            run_id: The run whose steps to read.

        Returns:
            Steps in execution order.
        """
        return self._steps.list_by_run(run_id)

    def record_steps(self, run_id: UUID, steps: list[dict[str, Any]]) -> list[RunStep]:
        """Store the per-step detail a runner reported.

        The run is fetched for its start time, which the steps table needs as
        half of the composite foreign key into the partitioned runs table.

        Args:
            run_id: The run these steps belong to.
            steps: Cleaned step mappings from
                :func:`~utils.validators.validate_steps_body`.

        Returns:
            The stored steps.

        Raises:
            NotFoundError: If no such run exists.
        """
        run = self.get_run(run_id)
        return self._steps.record_batch(
            run_id=run_id, run_started_at=run.started_at, steps=steps
        )

    # -- artifacts ----------------------------------------------------------
    def list_artifacts(self, run_id: UUID) -> list[RunArtifact]:
        """List a run's artifacts.

        Args:
            run_id: The run whose artifacts to read.

        Returns:
            The artifact metadata records.
        """
        return self._artifacts.list_by_run(run_id)

    def register_artifact(self, run_id: UUID, **artifact: Any) -> RunArtifact:
        """Record metadata for a file a runner produced.

        Args:
            run_id: The run that produced the file.
            **artifact: Cleaned fields from
                :func:`~utils.validators.validate_artifact_body`.

        Returns:
            The created artifact record.

        Raises:
            NotFoundError: If no such run exists.
        """
        run = self.get_run(run_id)
        return self._artifacts.create(
            run_id=run_id, run_started_at=run.started_at, **artifact
        )

    # -- comments -----------------------------------------------------------
    def list_comments(self, run_id: UUID) -> list[RunComment]:
        """List a run's comments.

        Args:
            run_id: The run whose comments to read.

        Returns:
            Comments in chronological order.
        """
        return self._comments.list_by_run(run_id)

    def add_comment(self, run_id: UUID, *, body: str, author_name: str) -> RunComment:
        """Add a comment to a run.

        Args:
            run_id: The run being commented on.
            body: Comment text, already validated.
            author_name: Free-text author name.

        Returns:
            The created comment.

        Raises:
            NotFoundError: If no such run exists.
        """
        run = self.get_run(run_id)
        return self._comments.create(
            run_id=run_id,
            run_started_at=run.started_at,
            author_name=author_name,
            body=body,
        )

    def delete_comment(self, comment_id: UUID) -> None:
        """Remove a comment.

        Args:
            comment_id: The comment to remove.

        Raises:
            NotFoundError: If it does not exist or was already removed.
        """
        if not self._comments.soft_delete(comment_id):
            raise NotFoundError("ההערה לא נמצאה")

    # -- export -------------------------------------------------------------
    def iter_export_rows(self, filters: dict[str, Any]) -> Iterator[dict[str, Any]]:
        """Stream matching runs for CSV export.

        Args:
            filters: Run filter with ``scope``, ``status`` and ``search`` keys.

        Yields:
            One row per matching run, streamed from a server-side cursor.
        """
        return self._runs.iter_for_export(
            scope=filters.get("scope"),
            status=filters.get("status"),
            search=filters.get("search"),
        )

    # -- maintenance --------------------------------------------------------
    def run_maintenance(self, *, retention_months: int) -> dict[str, Any]:
        """Provision partitions, apply retention and prune stale claims.

        Invoked by a scheduler. Retention drops whole partitions rather than
        deleting rows, which keeps it fast as history grows.

        Args:
            retention_months: Months of run history to keep.

        Returns:
            A summary with ``created``, ``dropped`` and ``claims_pruned``.
        """
        created = self._runs.ensure_partitions(months_ahead=3)
        cutoff = (datetime.now(UTC) - timedelta(days=retention_months * 31)).date()
        dropped = self._runs.drop_partitions_before(cutoff)
        pruned = self._runs.prune_idempotency_claims()

        logger.info(
            "maintenance complete",
            extra={"partitions": len(created), "dropped": dropped, "claims_pruned": pruned},
        )
        return {"created": created, "dropped": dropped, "claims_pruned": pruned}
