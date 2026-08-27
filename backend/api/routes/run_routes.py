"""Run endpoints.

Covers listing, triggering, cancellation, the live status stream, CSV export,
comments, and the reporting endpoints the automation suite calls to record what
actually happened: steps, artifacts and the final outcome.
"""

from __future__ import annotations

import csv
import io
import json
import time
from pathlib import Path
from typing import Final, Iterator

from flask import Blueprint, Response, jsonify, request, send_file, stream_with_context

from api.middleware import correlation_id, json_body
from api.serializers import (
    serialize_artifact,
    serialize_comment,
    serialize_page,
    serialize_run,
    serialize_step,
)
from services.run_service import RunService
from utils.errors import NotFoundError
from utils.validators import (
    optional_string,
    require_string,
    require_uuid,
    validate_artifact_body,
    validate_bulk_run_body,
    validate_comment_body,
    validate_complete_run_body,
    validate_run_list_query,
    validate_start_run_body,
    validate_steps_body,
)

run_bp = Blueprint("runs", __name__)

STREAM_INTERVAL_SECONDS: Final = 2
"""Seconds between live status frames.

Frequent enough to feel live, infrequent enough not to hammer the database from
every open dashboard.
"""

STREAM_MAX_SECONDS: Final = 300
"""Lifetime of a stream before it closes and the client reconnects.

Self-terminating stops connections accumulating behind a load balancer.
"""


def _service() -> RunService:
    """Build a run service for this request.

    Returns:
        A service instance with real repositories.
    """
    return RunService()


# ---------------------------------------------------------------------------
# Reads
# ---------------------------------------------------------------------------
@run_bp.get("/runs")
def list_runs() -> Response:
    """Return a page of runs.

    Query parameters:
        scope, status, search, from, to, sort, direction, limit, offset.

    Returns:
        HTTP 200 with ``items``, ``total``, ``limit`` and ``offset``.

    Raises:
        ValidationError: If any parameter is malformed or out of range.
    """
    filters = validate_run_list_query(request.args)
    page = _service().list_runs(**filters)
    return jsonify(serialize_page(page, serialize_run))


@run_bp.get("/runs/<run_id>")
def get_run(run_id: str) -> Response:
    """Load one run.

    Args:
        run_id: Path parameter identifying the run.

    Returns:
        HTTP 200 with the serialised run.

    Raises:
        ValidationError: If the identifier is not a UUID.
        NotFoundError: If no such run exists.
    """
    run = _service().get_run(require_uuid(run_id, "runId"))
    return jsonify(serialize_run(run))


# ---------------------------------------------------------------------------
# Triggering
# ---------------------------------------------------------------------------
@run_bp.post("/runs")
def start_run() -> tuple[Response, int]:
    """Enqueue one automation run.

    The body may identify the automation either by ``testDefinitionId`` or by
    ``runnerTarget``. The latter is what the automation suite uses, since it
    knows its own pytest node id but no database identifier.

    Returns:
        HTTP 202 with the queued run. A repeated idempotency key returns the
        original run rather than enqueueing a second.

    Raises:
        ValidationError: If the payload is malformed.
        NotFoundError: If the automation is unknown or unregistered.
        ConflictError: If it is inactive.
    """
    body = json_body()
    service = _service()

    runner_target = optional_string(body.get("runnerTarget"), "runnerTarget", max_length=300)
    if runner_target:
        run = service.start_run_by_target(
            runner_target=runner_target,
            idempotency_key=require_string(
                body.get("idempotencyKey"), "idempotencyKey", min_length=8, max_length=64
            ),
            triggered_by=optional_string(body.get("triggeredBy"), "triggeredBy", max_length=120)
            or "automation",
            trigger_source=optional_string(
                body.get("triggerSource"), "triggerSource", max_length=20
            )
            or "ci",
            correlation_id=correlation_id(),
        )
        return jsonify(serialize_run(run)), 202

    payload = validate_start_run_body(body)
    run = service.start_run(
        definition_id=payload["test_definition_id"],
        idempotency_key=payload["idempotency_key"],
        triggered_by=payload["triggered_by"],
        trigger_source=payload["trigger_source"],
        correlation_id=correlation_id(),
    )
    return jsonify(serialize_run(run)), 202


@run_bp.post("/runs/bulk")
def start_bulk_runs() -> tuple[Response, int]:
    """Enqueue the main test of every application in scope.

    Returns:
        HTTP 202 with ``started``, an array of the queued runs.

    Raises:
        ValidationError: If the payload is malformed, or the scope is the general
            scope — refused because bulk-firing automation that changes
            production state is exactly the accident worth preventing.
    """
    payload = validate_bulk_run_body(json_body())
    started = _service().start_bulk_main(
        scope=payload["scope"],
        idempotency_key=payload["idempotency_key"],
        triggered_by=payload["triggered_by"],
        correlation_id=correlation_id(),
    )
    return jsonify({"started": [serialize_run(run) for run in started]}), 202


@run_bp.post("/runs/<run_id>/cancel")
def cancel_run(run_id: str) -> Response:
    """Cancel an in-flight run.

    Args:
        run_id: Path parameter identifying the run.

    Returns:
        HTTP 200 with the cancelled run.

    Raises:
        ValidationError: If the identifier is malformed.
        NotFoundError: If no such run exists.
        ConflictError: If it had already finished.
    """
    actor = optional_string(json_body().get("actorName"), "actorName", max_length=120) or "מפעיל"
    run = _service().cancel_run(require_uuid(run_id, "runId"), actor)
    return jsonify(serialize_run(run))


# ---------------------------------------------------------------------------
# Runner reporting — how automation results reach the database
# ---------------------------------------------------------------------------
@run_bp.post("/runs/<run_id>/claim")
def claim_run(run_id: str) -> Response:
    """Mark a queued run as running.

    Args:
        run_id: Path parameter identifying the run.

    Returns:
        HTTP 200 with the run, now marked running.

    Raises:
        ValidationError: If the identifier or payload is malformed.
        ConflictError: If the run was not queued.
    """
    worker_id = require_string(json_body().get("workerId"), "workerId", max_length=120)
    run = _service().claim_run(require_uuid(run_id, "runId"), worker_id)
    return jsonify(serialize_run(run))


@run_bp.post("/runs/<run_id>/complete")
def complete_run(run_id: str) -> Response:
    """Record the outcome of a run.

    Args:
        run_id: Path parameter identifying the run.

    Returns:
        HTTP 200 with the completed run.

    Raises:
        ValidationError: If the payload is malformed, or a failure is reported
            without a reason.
        ConflictError: If the run had already finished.
    """
    payload = validate_complete_run_body(json_body())
    run = _service().complete_run(require_uuid(run_id, "runId"), **payload)
    return jsonify(serialize_run(run))


@run_bp.get("/runs/<run_id>/steps")
def list_steps(run_id: str) -> Response:
    """List a run's per-step detail.

    Args:
        run_id: Path parameter identifying the run.

    Returns:
        HTTP 200 with an array of steps in execution order.

    Raises:
        ValidationError: If the identifier is malformed.
    """
    steps = _service().list_steps(require_uuid(run_id, "runId"))
    return jsonify([serialize_step(step) for step in steps])


@run_bp.post("/runs/<run_id>/steps")
def record_steps(run_id: str) -> tuple[Response, int]:
    """Record a batch of steps for a run.

    Posted as one batch rather than one request per step, so a twenty-step
    automation costs a single round trip.

    Args:
        run_id: Path parameter identifying the run.

    Returns:
        HTTP 201 with the stored steps.

    Raises:
        ValidationError: If the payload is malformed.
        NotFoundError: If no such run exists.
    """
    steps = validate_steps_body(json_body())
    stored = _service().record_steps(require_uuid(run_id, "runId"), steps)
    return jsonify([serialize_step(step) for step in stored]), 201


@run_bp.get("/runs/<run_id>/artifacts")
def list_artifacts(run_id: str) -> Response:
    """List a run's artifacts.

    Args:
        run_id: Path parameter identifying the run.

    Returns:
        HTTP 200 with an array of serialised artifacts.

    Raises:
        ValidationError: If the identifier is malformed.
    """
    artifacts = _service().list_artifacts(require_uuid(run_id, "runId"))
    return jsonify([serialize_artifact(artifact) for artifact in artifacts])


@run_bp.post("/runs/<run_id>/artifacts")
def register_artifact(run_id: str) -> tuple[Response, int]:
    """Record metadata for a file the runner produced.

    Args:
        run_id: Path parameter identifying the run.

    Returns:
        HTTP 201 with the created artifact record.

    Raises:
        ValidationError: If the payload is malformed, or neither a local path nor
            an object key was supplied.
        NotFoundError: If no such run exists.
    """
    payload = validate_artifact_body(json_body())
    artifact = _service().register_artifact(require_uuid(run_id, "runId"), **payload)
    return jsonify(serialize_artifact(artifact)), 201


@run_bp.get("/runs/<run_id>/artifacts/<artifact_id>/download")
def download_artifact(run_id: str, artifact_id: str) -> Response:
    """Serve an artifact stored on the local filesystem.

    Args:
        run_id: Path parameter identifying the run.
        artifact_id: Path parameter identifying the artifact.

    Returns:
        The file, as an attachment.

    Raises:
        ValidationError: If either identifier is malformed.
        NotFoundError: If the artifact is unknown, has no local path, or the file
            is missing from disk.
    """
    target_id = require_uuid(artifact_id, "artifactId")
    artifacts = _service().list_artifacts(require_uuid(run_id, "runId"))

    match = next((entry for entry in artifacts if entry.id == target_id), None)
    if match is None or not match.local_path:
        raise NotFoundError("הקובץ לא נמצא")

    path = Path(match.local_path)
    if not path.is_file():
        raise NotFoundError("הקובץ אינו קיים בשרת")

    return send_file(path, as_attachment=True, download_name=match.file_name)


# ---------------------------------------------------------------------------
# Live status
# ---------------------------------------------------------------------------
@run_bp.get("/runs/stream")
def stream_runs() -> Response:
    """Stream live run status as server-sent events.

    Server-sent events rather than WebSockets: the traffic is one-directional and
    the transport reconnects natively. Elapsed seconds are computed server-side,
    so a backgrounded tab shows the correct value the moment it returns.

    Returns:
        An HTTP 200 ``text/event-stream`` response. A comment frame between
        batches stops a proxy closing an idle connection, and the stream ends
        after :data:`STREAM_MAX_SECONDS` so the client reconnects.
    """
    service = _service()

    def generate() -> Iterator[str]:
        """Yield event frames until the stream's lifetime elapses.

        Yields:
            Server-sent event frames, each terminated by a blank line.
        """
        started = time.monotonic()

        while time.monotonic() - started < STREAM_MAX_SECONDS:
            for update in service.list_active_runs():
                yield f"data: {json.dumps(update, ensure_ascii=False)}\n\n"

            yield ": keep-alive\n\n"
            time.sleep(STREAM_INTERVAL_SECONDS)

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            # Without this, nginx buffers the stream and nothing arrives live.
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------
@run_bp.get("/runs/<run_id>/comments")
def list_comments(run_id: str) -> Response:
    """List a run's comments.

    Args:
        run_id: Path parameter identifying the run.

    Returns:
        HTTP 200 with an array of comments, oldest first.

    Raises:
        ValidationError: If the identifier is malformed.
    """
    comments = _service().list_comments(require_uuid(run_id, "runId"))
    return jsonify([serialize_comment(comment) for comment in comments])


@run_bp.post("/runs/<run_id>/comments")
def add_comment(run_id: str) -> tuple[Response, int]:
    """Add a comment to a run.

    Args:
        run_id: Path parameter identifying the run.

    Returns:
        HTTP 201 with the created comment.

    Raises:
        ValidationError: If the identifier or comment text is malformed.
        NotFoundError: If no such run exists.
    """
    payload = validate_comment_body(json_body())
    comment = _service().add_comment(require_uuid(run_id, "runId"), **payload)
    return jsonify(serialize_comment(comment)), 201


@run_bp.delete("/runs/<run_id>/comments/<comment_id>")
def delete_comment(run_id: str, comment_id: str) -> tuple[str, int]:
    """Remove a comment.

    Args:
        run_id: Path parameter identifying the run, validated for consistency.
        comment_id: Path parameter identifying the comment.

    Returns:
        HTTP 204 with an empty body.

    Raises:
        ValidationError: If either identifier is malformed.
        NotFoundError: If the comment does not exist or was already removed.
    """
    require_uuid(run_id, "runId")
    _service().delete_comment(require_uuid(comment_id, "commentId"))
    return "", 204


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------
@run_bp.get("/runs/export")
def export_runs() -> Response:
    """Stream matching runs as CSV.

    Streamed rather than enqueued as a job: rows come from a server-side cursor,
    so memory stays flat however large the history, and the caller gets a file
    immediately.

    Query parameters:
        Same filters as the run list.

    Returns:
        An HTTP 200 ``text/csv`` attachment.

    Raises:
        ValidationError: If any filter is malformed.
    """
    filters = validate_run_list_query(request.args)
    service = _service()

    columns = [
        "id", "test_name", "runner_target", "scope_label", "status",
        "started_at", "ended_at", "duration_seconds", "triggered_by",
        "trigger_source", "total_steps", "failed_steps",
        "failure_feature", "failure_error_type", "failure_reason",
    ]

    def generate() -> Iterator[str]:
        """Yield the CSV header then one line per run.

        Yields:
            CSV text, a line at a time.
        """
        buffer = io.StringIO()
        writer = csv.writer(buffer)

        # A BOM so Excel opens the Hebrew columns as UTF-8 rather than mojibake.
        yield "\ufeff"

        writer.writerow(columns)
        yield buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)

        for row in service.iter_export_rows(filters):
            writer.writerow([row.get(column, "") for column in columns])
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)

    return Response(
        stream_with_context(generate()),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="noc-runs.csv"'},
    )
