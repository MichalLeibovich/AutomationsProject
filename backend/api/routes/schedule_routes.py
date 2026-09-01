"""Scheduled-automation endpoints.

Covers what the interface needs — upcoming occurrences, recently completed
ones, skip/restore, adding or removing a one-off extra run — plus the single
endpoint the worker calls on a timer to actually fire due occurrences.
"""

from __future__ import annotations

from flask import Blueprint, Response, jsonify, request

from api.middleware import json_body
from api.serializers import (
    serialize_extra_run,
    serialize_occurrence,
    serialize_run_group,
    serialize_schedule,
)
from services.schedule_service import ScheduleService
from utils.validators import (
    require_uuid,
    validate_extra_run_body,
    validate_frequency_body,
    validate_occurrence_body,
    validate_recent_query,
    validate_upcoming_query,
)

schedule_bp = Blueprint("schedules", __name__)


def _service() -> ScheduleService:
    """Build a schedule service for this request.

    Returns:
        A service instance with real repositories.
    """
    return ScheduleService()


@schedule_bp.get("/schedules")
def list_schedules() -> Response:
    """List every active recurring schedule.

    Returns:
        HTTP 200 with an array of schedules.
    """
    return jsonify([serialize_schedule(schedule) for schedule in _service().list_schedules()])


@schedule_bp.get("/schedules/upcoming")
def list_upcoming() -> Response:
    """List every occurrence due in the requested window.

    Query parameters:
        hours: How far ahead to look. Defaults to 24.

    Returns:
        HTTP 200 with occurrences in ascending order, including skipped ones.

    Raises:
        ValidationError: If ``hours`` is out of range.
    """
    params = validate_upcoming_query(request.args)
    occurrences = _service().list_upcoming(**params)
    return jsonify([serialize_occurrence(occurrence) for occurrence in occurrences])


@schedule_bp.get("/schedules/recent")
def list_recent() -> Response:
    """List the most recently completed scheduled occurrences, grouped by slot.

    Query parameters:
        limit: Maximum groups to return. Defaults to 8.

    Returns:
        HTTP 200 with groups in descending order, most recent first.

    Raises:
        ValidationError: If ``limit`` is out of range.
    """
    params = validate_recent_query(request.args)
    groups = _service().list_recent(**params)
    return jsonify([serialize_run_group(group) for group in groups])


@schedule_bp.patch("/schedules/<schedule_id>/frequency")
def update_frequency(schedule_id: str) -> Response:
    """Change a schedule's cadence, without touching its committed next run.

    The old cadence keeps producing whichever occurrence is already next;
    the new one only starts counting occurrences after that instant.

    Args:
        schedule_id: Path parameter identifying the schedule.

    Returns:
        HTTP 200 with the updated schedule.

    Raises:
        ValidationError: If the identifier or body is malformed.
        NotFoundError: If no such schedule exists.
    """
    payload = validate_frequency_body(json_body())
    schedule = _service().update_frequency(require_uuid(schedule_id, "scheduleId"), **payload)
    return jsonify(serialize_schedule(schedule))


@schedule_bp.post("/schedules/<schedule_id>/skip")
def skip_occurrence(schedule_id: str) -> tuple[str, int]:
    """Cancel one occurrence of a recurring schedule.

    Args:
        schedule_id: Path parameter identifying the schedule.

    Returns:
        HTTP 204 with an empty body.

    Raises:
        ValidationError: If the identifier or body is malformed.
        NotFoundError: If no such schedule exists.
    """
    payload = validate_occurrence_body(json_body())
    _service().skip(require_uuid(schedule_id, "scheduleId"), payload["occurrence"])
    return "", 204


@schedule_bp.post("/schedules/<schedule_id>/restore")
def restore_occurrence(schedule_id: str) -> tuple[str, int]:
    """Undo a skip.

    Args:
        schedule_id: Path parameter identifying the schedule.

    Returns:
        HTTP 204 with an empty body.

    Raises:
        ValidationError: If the identifier or body is malformed.
        NotFoundError: If no such schedule exists, or the occurrence was not
            skipped.
    """
    payload = validate_occurrence_body(json_body())
    _service().restore(require_uuid(schedule_id, "scheduleId"), payload["occurrence"])
    return "", 204


@schedule_bp.post("/schedules/extra")
def add_extra_run() -> tuple[Response, int]:
    """Schedule one one-off run, outside any recurring schedule.

    Returns:
        HTTP 201 with the created extra run.

    Raises:
        ValidationError: If the payload is malformed, or ``runAt`` is in the
            past.
        NotFoundError: If the application does not exist.
    """
    payload = validate_extra_run_body(json_body())
    extra_run = _service().add_extra(**payload)
    return jsonify(serialize_extra_run(extra_run)), 201


@schedule_bp.delete("/schedules/extra/<extra_run_id>")
def remove_extra_run(extra_run_id: str) -> tuple[str, int]:
    """Remove a one-off run before it fires.

    Args:
        extra_run_id: Path parameter identifying the extra run.

    Returns:
        HTTP 204 with an empty body.

    Raises:
        ValidationError: If the identifier is malformed.
        NotFoundError: If it does not exist, or had already fired.
    """
    _service().remove_extra(require_uuid(extra_run_id, "extraRunId"))
    return "", 204


@schedule_bp.post("/schedules/tick")
def tick() -> Response:
    """Enqueue every occurrence that has come due.

    Called by the worker on a timer, not by the interface. Safe to call from
    multiple worker replicas at once and safe to call more often than
    strictly necessary — every enqueue is idempotent, keyed by the schedule
    (or extra run) and the occurrence.

    Returns:
        HTTP 200 with the number of runs this call created.
    """
    return jsonify(_service().tick())
