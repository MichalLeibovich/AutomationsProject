"""Dashboard and calendar endpoints."""

from __future__ import annotations

from datetime import UTC, datetime

from flask import Blueprint, Response, jsonify, request

from services.analytics_service import AnalyticsService
from utils.validators import validate_calendar_query, validate_dashboard_query

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.get("/analytics/dashboard")
def dashboard() -> Response:
    """Return the aggregated dashboard payload.

    Query parameters:
        scope: Absent for all applications, ``general``, or an application name.
        range: ``hour``, ``day``, ``week`` or ``custom``. Defaults to ``week``.
        from: Start bound, required when ``range`` is ``custom``.
        to: End bound, required when ``range`` is ``custom``.

    Returns:
        HTTP 200 with statistics, the volume series and both failure breakdowns.

    Raises:
        ValidationError: If a parameter is malformed, or a custom range is
            missing a bound.
    """
    query = validate_dashboard_query(request.args)
    payload = AnalyticsService().get_dashboard(
        scope=query["scope"],
        range_preset=query["range"],
        date_from=query["date_from"],
        date_to=query["date_to"],
    )
    return jsonify(payload)


@analytics_bp.get("/analytics/calendar")
def calendar() -> Response:
    """Return aggregated run activity for one month.

    Query parameters:
        year: Four-digit year. Defaults to the current year.
        month: Month number, 1 to 12. Defaults to the current month.

    Defaulting both keeps the first page load parameterless.

    Returns:
        HTTP 200 with an array of days that had runs, each carrying totals and a
        short preview for the day cell.

    Raises:
        ValidationError: If either parameter is non-numeric or out of range.
    """
    query = validate_calendar_query(request.args)

    now = datetime.now(UTC)
    year = query["year"] or now.year
    month = query["month"] or now.month

    return jsonify(AnalyticsService().get_calendar_month(year=year, month=month))


@analytics_bp.post("/analytics/refresh")
def refresh_views() -> Response:
    """Refresh the daily statistics rollup.

    Exposed so a scheduler can trigger it over HTTP rather than needing database
    credentials of its own.

    Returns:
        HTTP 200 with the refresh mode used.
    """
    return jsonify({"mode": AnalyticsService().refresh_materialized_views()})
