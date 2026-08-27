"""Dashboard and calendar aggregation.

Aggregation is pushed into PostgreSQL rather than performed in Python: counting
hundreds of thousands of rows in the application would mean transferring them
first.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from database import queries
from database.connection import read_only
from repositories.base_repository import BaseRepository
from utils.constants import (
    ALLOWED_BUCKETS,
    BUCKET_STEPS,
    CALENDAR_PREVIEW_LIMIT,
    FAILURE_DIMENSIONS,
    FEATURE_COLORS,
)
from utils.errors import ValidationError
from utils.helpers import bucket_label, pass_rate, resolve_range
from utils.logger import get_logger

logger = get_logger(__name__)


class AnalyticsService(BaseRepository):
    """Serves the aggregated views behind the dashboard and calendar.

    Extends :class:`~repositories.base_repository.BaseRepository` directly rather
    than composing one: this is read-only aggregation returning response payloads
    rather than domain models, so a separate repository would only forward calls.
    """

    def get_dashboard(
        self,
        *,
        scope: str | None,
        range_preset: str,
        date_from: datetime | None,
        date_to: datetime | None,
    ) -> dict[str, Any]:
        """Build the complete dashboard payload.

        All four aggregates run on one connection, so every panel reflects the
        same transaction snapshot and the figures cannot disagree.

        Args:
            scope: None for all applications, ``"general"``, or an application
                name.
            range_preset: ``"hour"``, ``"day"``, ``"week"`` or ``"custom"``.
            date_from: Start bound, required only for a custom range.
            date_to: End bound, required only for a custom range.

        Returns:
            A camelCase payload with ``stats``, ``volume``, ``failuresByFeature``
            and ``failuresByErrorType``. Feature colours are resolved here so a
            cause looks identical in every chart and in the legend.

        Raises:
            ValidationError: If a custom range is missing a bound, or the
                resolved bucket granularity is unsupported.
        """
        try:
            start, end, bucket = resolve_range(range_preset, date_from, date_to)
        except ValueError as exc:
            raise ValidationError("טווח מותאם מחייב תאריך התחלה וסיום") from exc

        if bucket not in ALLOWED_BUCKETS:
            raise ValidationError("רזולוציית זמן אינה נתמכת")

        params = {
            "scope": scope,
            "status": None,
            "search": None,
            "date_from": start,
            "date_to": end,
        }

        with read_only() as cursor:
            cursor.execute(queries.DASHBOARD_STATS, params)
            stats_row = dict(cursor.fetchone() or {})

            # The step travels as a bound parameter; the bucket name only
            # selects it, and was validated against the whitelist above.
            cursor.execute(
                queries.build_volume_query(), {**params, "step": BUCKET_STEPS[bucket]}
            )
            volume_rows = [dict(row) for row in cursor.fetchall()]

            cursor.execute(
                queries.build_failures_by_dimension_query(FAILURE_DIMENSIONS["feature"]), params
            )
            feature_rows = [dict(row) for row in cursor.fetchall()]

            cursor.execute(
                queries.build_failures_by_dimension_query(FAILURE_DIMENSIONS["error_type"]),
                params,
            )
            error_rows = [dict(row) for row in cursor.fetchall()]

        total = int(stats_row.get("total_runs") or 0)
        failed = int(stats_row.get("failed_runs") or 0)

        return {
            "stats": {
                "totalRuns": total,
                "failedRuns": failed,
                "passRate": pass_rate(total, failed),
                "averageDurationSeconds": int(stats_row.get("avg_duration_seconds") or 0),
            },
            "volume": [
                {
                    "label": bucket_label(row["bucket_start"], bucket),
                    "bucketStart": row["bucket_start"].isoformat(),
                    "passed": int(row["passed"]),
                    "failed": int(row["failed"]),
                }
                for row in volume_rows
            ],
            "failuresByFeature": [
                {
                    "name": row["name"],
                    "count": int(row["count"]),
                    "color": FEATURE_COLORS.get(row["name"]),
                }
                for row in feature_rows
            ],
            "failuresByErrorType": [
                {"name": row["name"], "count": int(row["count"]), "color": None}
                for row in error_rows
            ],
        }

    def get_calendar_month(self, *, year: int, month: int) -> list[dict[str, Any]]:
        """Aggregate one month of run activity.

        A single query computes day totals and the bounded per-day preview
        together, rather than issuing a query per day.

        Args:
            year: Four-digit year.
            month: Month number, 1 to 12.

        Returns:
            One camelCase mapping per day that had runs, ordered by date.
        """
        rows = self.fetch_all(
            queries.CALENDAR_MONTH,
            {"year": year, "month": month, "preview_limit": CALENDAR_PREVIEW_LIMIT},
        )

        return [
            {
                "date": row["day"].isoformat(),
                "total": int(row["total"]),
                "passed": int(row["passed"]),
                "failed": int(row["failed"]),
                "preview": row["preview"] or [],
            }
            for row in rows
        ]

    def refresh_materialized_views(self) -> str:
        """Refresh the daily statistics rollup.

        The database function selects the refresh mode, since the preconditions
        for a concurrent refresh can only be checked reliably in the same
        transaction as the refresh itself.

        Returns:
            The mode used, ``"concurrent"`` or ``"blocking"``.
        """
        row = self.execute_returning(queries.REFRESH_DAILY_RUN_STATS) or {}
        mode = str(row.get("mode", "unknown"))
        logger.info("materialized view refreshed", extra={"mode": mode})
        return mode
