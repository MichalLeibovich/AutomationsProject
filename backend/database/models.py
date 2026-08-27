"""Domain entities returned by the repository layer.

Plain frozen dataclasses rather than an ORM: the SQL is hand-written and
partition-aware, so models exist only to give the layers above a typed object
instead of a bare mapping. Each ``from_row`` is the single place a column name
maps to a field, so a column rename does not ripple outward.

Slots are enabled because a busy list endpoint constructs thousands of these per
request.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Mapping
from uuid import UUID


def _uuid(value: Any) -> UUID | None:
    """Coerce a value to a UUID.

    Args:
        value: A UUID, a string, or None.

    Returns:
        The UUID, or None.

    Raises:
        ValueError: If a non-null value is not a valid UUID.
    """
    if value is None:
        return None
    return value if isinstance(value, UUID) else UUID(str(value))


@dataclass(frozen=True, slots=True)
class Application:
    """A monitored application.

    Attributes:
        id: Primary key.
        name: Display name, also the scope identifier in the interface.
        slug: Stable URL-safe identifier, used for upserts.
        color: Identity colour as ``#RRGGBB``, consistent across every view.
        display_order: Sort position in the filter row and grid.
        is_active: Whether it appears in the interface. Deactivated rows are
            retained because run history references them.
    """

    id: UUID
    name: str
    slug: str
    color: str
    display_order: int
    is_active: bool

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> "Application":
        """Build an application from a database row.

        Args:
            row: Row with ``id``, ``name``, ``slug`` and ``color``.

        Returns:
            The mapped application.

        Raises:
            KeyError: If a mandatory column is absent.
        """
        return cls(
            id=_uuid(row["id"]),  # type: ignore[arg-type]
            name=row["name"],
            slug=str(row["slug"]),
            color=row["color"],
            display_order=row.get("display_order", 0),
            is_active=row.get("is_active", True),
        )


@dataclass(frozen=True, slots=True)
class TestDefinition:
    """A runnable automation.

    Attributes:
        id: Primary key.
        application_id: Owning application. None for general automation.
        scope: ``"application"`` or ``"general"``.
        kind: ``"main"``, ``"secondary"`` or ``"general"``.
        name: Display name.
        description: Optional longer description.
        runner_target: pytest node id the runner executes, for example
            ``tests/test_login.py::test_valid_login``. This is what ties the row
            to an automation on disk.
        display_order: Sort position within its card.
        timeout_seconds: Runner timeout before the run is marked timed out.
        is_active: Whether it may be triggered.
        application_name: Owning application's name, populated when the query
            joins it. Used to freeze the scope label onto a new run.
    """

    id: UUID
    application_id: UUID | None
    scope: str
    kind: str
    name: str
    description: str | None
    runner_target: str
    display_order: int
    timeout_seconds: int
    is_active: bool
    application_name: str | None = None

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> "TestDefinition":
        """Build a definition from a database row.

        Args:
            row: Row with ``id``, ``scope``, ``kind``, ``name`` and
                ``runner_target``.

        Returns:
            The mapped definition.

        Raises:
            KeyError: If a mandatory column is absent.
        """
        return cls(
            id=_uuid(row["id"]),  # type: ignore[arg-type]
            application_id=_uuid(row.get("application_id")),
            scope=row["scope"],
            kind=row["kind"],
            name=row["name"],
            description=row.get("description"),
            runner_target=row["runner_target"],
            display_order=row.get("display_order", 0),
            timeout_seconds=row.get("timeout_seconds", 600),
            is_active=row.get("is_active", True),
            application_name=row.get("application_name"),
        )


@dataclass(frozen=True, slots=True)
class RunFailure:
    """Why a run failed.

    Attributes:
        feature: Component that failed, driving the failures-by-feature chart.
        error_type: Failure category, driving the error-type breakdown.
        reason: Human-readable explanation shown in the debrief.
        stack_trace: Full traceback, when the runner captured one.
    """

    feature: str | None
    error_type: str | None
    reason: str
    stack_trace: str | None = None


@dataclass(frozen=True, slots=True)
class TestRun:
    """One execution of an automation.

    Attributes:
        id: Primary key. With ``started_at`` it forms the partitioned table's
            composite key.
        test_definition_id: Definition that was executed.
        test_name: Definition name, frozen at insert time.
        runner_target: pytest node id that was run, frozen at insert time.
        application_id: Owning application. None for general automation.
        scope: ``"application"`` or ``"general"``.
        scope_label: Application name or the general label, frozen at insert time
            so renaming an application never rewrites history.
        status: Current status.
        queued_at: When it was enqueued.
        started_at: When execution began. Also the partition key.
        ended_at: When execution finished, or None while in flight.
        duration_seconds: Elapsed seconds, generated by the database.
        triggered_by: Free text — a hostname, a CI job, or ``"manual"``.
        trigger_source: How it was triggered.
        worker_id: Identifier of the worker that claimed it.
        attempt: Attempt number for this definition.
        total_steps: Steps reported by the runner.
        failed_steps: Steps that failed.
        artifact_count: Artifacts stored.
        failure: Failure detail, or None when the run did not fail.
    """

    id: UUID
    test_definition_id: UUID
    test_name: str
    runner_target: str
    application_id: UUID | None
    scope: str
    scope_label: str
    status: str
    queued_at: datetime | None
    started_at: datetime
    ended_at: datetime | None
    duration_seconds: int | None
    triggered_by: str
    trigger_source: str
    worker_id: str | None
    attempt: int
    total_steps: int
    failed_steps: int
    artifact_count: int
    failure: RunFailure | None = None

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> "TestRun":
        """Build a run from a database row.

        A :class:`RunFailure` is attached only when a reason is present, so a
        passing run carries no empty failure object.

        Args:
            row: Row from the shared run projection.

        Returns:
            The mapped run.

        Raises:
            KeyError: If a mandatory column is absent.
        """
        reason = row.get("failure_reason")
        failure = (
            RunFailure(
                feature=row.get("failure_feature"),
                error_type=row.get("failure_error_type"),
                reason=reason,
                stack_trace=row.get("stack_trace"),
            )
            if reason
            else None
        )

        return cls(
            id=_uuid(row["id"]),  # type: ignore[arg-type]
            test_definition_id=_uuid(row["test_definition_id"]),  # type: ignore[arg-type]
            test_name=row["test_name"],
            runner_target=row.get("runner_target", ""),
            application_id=_uuid(row.get("application_id")),
            scope=row["scope"],
            scope_label=row["scope_label"],
            status=row["status"],
            queued_at=row.get("queued_at"),
            started_at=row["started_at"],
            ended_at=row.get("ended_at"),
            duration_seconds=row.get("duration_seconds"),
            triggered_by=row.get("triggered_by", "manual"),
            trigger_source=row.get("trigger_source", "manual"),
            worker_id=row.get("worker_id"),
            attempt=row.get("attempt", 1),
            total_steps=row.get("total_steps", 0),
            failed_steps=row.get("failed_steps", 0),
            artifact_count=row.get("artifact_count", 0),
            failure=failure,
        )

    @property
    def is_active(self) -> bool:
        """Whether the run is still queued or executing."""
        return self.status in {"queued", "running"}


@dataclass(frozen=True, slots=True)
class RunStep:
    """One step within an automation run.

    Attributes:
        id: Primary key.
        run_id: Owning run.
        step_index: Zero-based position within the run.
        name: What the step did.
        status: ``"passed"``, ``"failed"`` or ``"skipped"``.
        duration_ms: How long the step took.
        error_message: Failure detail, when the step failed.
        started_at: When the step began.
    """

    id: UUID
    run_id: UUID
    step_index: int
    name: str
    status: str
    duration_ms: int
    error_message: str | None
    started_at: datetime

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> "RunStep":
        """Build a step from a database row.

        Args:
            row: Row with the step columns.

        Returns:
            The mapped step.

        Raises:
            KeyError: If a mandatory column is absent.
        """
        return cls(
            id=_uuid(row["id"]),  # type: ignore[arg-type]
            run_id=_uuid(row["run_id"]),  # type: ignore[arg-type]
            step_index=row["step_index"],
            name=row["name"],
            status=row["status"],
            duration_ms=row.get("duration_ms", 0),
            error_message=row.get("error_message"),
            started_at=row["started_at"],
        )


@dataclass(frozen=True, slots=True)
class RunArtifact:
    """A file produced by a run.

    Only metadata is stored relationally; the bytes live on disk or in object
    storage.

    Attributes:
        id: Primary key.
        run_id: Owning run.
        kind: screenshot, log, trace, video, har or report.
        file_name: Original file name.
        local_path: Path on a shared filesystem, when used.
        s3_bucket: Bucket holding the object, when used.
        s3_key: Object key, when used.
        content_type: MIME type.
        size_bytes: File size.
    """

    id: UUID
    run_id: UUID
    kind: str
    file_name: str
    local_path: str | None
    s3_bucket: str | None
    s3_key: str | None
    content_type: str
    size_bytes: int

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> "RunArtifact":
        """Build an artifact from a database row.

        Args:
            row: Row with the artifact columns.

        Returns:
            The mapped artifact.

        Raises:
            KeyError: If a mandatory column is absent.
        """
        return cls(
            id=_uuid(row["id"]),  # type: ignore[arg-type]
            run_id=_uuid(row["run_id"]),  # type: ignore[arg-type]
            kind=row["kind"],
            file_name=row["file_name"],
            local_path=row.get("local_path"),
            s3_bucket=row.get("s3_bucket"),
            s3_key=row.get("s3_key"),
            content_type=row.get("content_type", "application/octet-stream"),
            size_bytes=row.get("size_bytes", 0),
        )


@dataclass(frozen=True, slots=True)
class RunComment:
    """An operator note attached to a run.

    Attributes:
        id: Primary key.
        run_id: Run the comment belongs to.
        author_name: Free-text author name; there are no accounts.
        body: Comment text.
        created_at: When it was written.
    """

    id: UUID
    run_id: UUID
    author_name: str
    body: str
    created_at: datetime

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> "RunComment":
        """Build a comment from a database row.

        Args:
            row: Row with the comment columns.

        Returns:
            The mapped comment.

        Raises:
            KeyError: If a mandatory column is absent.
        """
        return cls(
            id=_uuid(row["id"]),  # type: ignore[arg-type]
            run_id=_uuid(row["run_id"]),  # type: ignore[arg-type]
            author_name=row["author_name"],
            body=row["body"],
            created_at=row["created_at"],
        )


@dataclass(frozen=True, slots=True)
class CalendarDay:
    """Aggregated run activity for one calendar day.

    Attributes:
        day: The date.
        total: Runs started that day.
        passed: Runs that passed.
        failed: Runs that failed.
        preview: A bounded sample for the day cell.
    """

    day: date
    total: int
    passed: int
    failed: int
    preview: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> "CalendarDay":
        """Build a calendar day from a database row.

        Args:
            row: Row with ``day``, totals and an optional ``preview`` array.

        Returns:
            The mapped day.

        Raises:
            KeyError: If a mandatory column is absent.
        """
        return cls(
            day=row["day"],
            total=int(row["total"]),
            passed=int(row["passed"]),
            failed=int(row["failed"]),
            preview=list(row.get("preview") or []),
        )


@dataclass(frozen=True, slots=True)
class Page:
    """A slice of results with the total match count.

    Attributes:
        items: Rows for this page, already mapped to domain models.
        total: Rows matching the filter, ignoring pagination.
        limit: Page size applied.
        offset: Row offset applied.
    """

    items: list[Any]
    total: int
    limit: int
    offset: int
