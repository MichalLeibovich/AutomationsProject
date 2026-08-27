"""Domain constants shared across every layer.

Single source of truth for the enumerated values that also appear in
``database/schema.sql``. Sorting and aggregation whitelists live here so no
request value can ever reach SQL text.
"""

from __future__ import annotations

from typing import Final

# ---------------------------------------------------------------------------
# Scope and kind
# ---------------------------------------------------------------------------
SCOPE_APPLICATION: Final = "application"
SCOPE_GENERAL: Final = "general"

KIND_MAIN: Final = "main"
KIND_SECONDARY: Final = "secondary"
KIND_GENERAL: Final = "general"

GENERAL_SCOPE_LABEL: Final = "כללי"
"""Scope label written to general-scope runs, frozen at insert time."""

# ---------------------------------------------------------------------------
# Run status
# ---------------------------------------------------------------------------
STATUS_QUEUED: Final = "queued"
STATUS_RUNNING: Final = "running"
STATUS_PASSED: Final = "passed"
STATUS_FAILED: Final = "failed"
STATUS_CANCELLED: Final = "cancelled"
STATUS_TIMED_OUT: Final = "timed_out"

ACTIVE_STATUSES: Final[frozenset[str]] = frozenset({STATUS_QUEUED, STATUS_RUNNING})
"""Statuses for which a run is still in flight."""

TERMINAL_STATUSES: Final[frozenset[str]] = frozenset(
    {STATUS_PASSED, STATUS_FAILED, STATUS_CANCELLED, STATUS_TIMED_OUT}
)
"""Statuses from which no further transition is permitted."""

ALL_STATUSES: Final[tuple[str, ...]] = (
    STATUS_QUEUED, STATUS_RUNNING, STATUS_PASSED,
    STATUS_FAILED, STATUS_CANCELLED, STATUS_TIMED_OUT,
)
"""Every persisted run status."""

# ---------------------------------------------------------------------------
# Triggers, artifacts, steps
# ---------------------------------------------------------------------------
TRIGGER_MANUAL: Final = "manual"
TRIGGER_BULK: Final = "bulk"
TRIGGER_SCHEDULE: Final = "schedule"
TRIGGER_CI: Final = "ci"
TRIGGER_API: Final = "api"

ALL_TRIGGER_SOURCES: Final[tuple[str, ...]] = (
    TRIGGER_MANUAL, TRIGGER_BULK, TRIGGER_SCHEDULE, TRIGGER_CI, TRIGGER_API,
)

ARTIFACT_KINDS: Final[tuple[str, ...]] = (
    "screenshot", "log", "trace", "video", "har", "report",
)

STEP_STATUSES: Final[tuple[str, ...]] = ("passed", "failed", "skipped")

# ---------------------------------------------------------------------------
# Sorting
# ---------------------------------------------------------------------------
SORTABLE_RUN_COLUMNS: Final[dict[str, str]] = {
    "started_at": "started_at",
    "duration_seconds": "duration_seconds",
    "status": "status",
}
"""Maps an accepted sort key to its column name.

A whitelist, so a request value resolves to a known identifier rather than
being interpolated into query text.
"""

SORT_DIRECTIONS: Final[dict[str, str]] = {"asc": "ASC", "desc": "DESC"}
"""Maps an accepted direction to its SQL keyword."""

# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------
FAILURE_DIMENSIONS: Final[dict[str, str]] = {
    "feature": "failure_feature",
    "error_type": "failure_error_type",
}
"""Maps a failure-breakdown dimension to the column it aggregates."""

FEATURE_COLORS: Final[dict[str, str]] = {
    "התחברות": "#3B82F6",
    "ניווט": "#10B981",
    "טעינת נתונים": "#F59E0B",
    "API": "#EF4444",
    "בקרת גישה": "#8B5CF6",
}
"""Stable colour per failure feature, so a cause looks identical in every chart."""

BUCKET_MINUTE: Final = "minute"
BUCKET_HOUR: Final = "hour"
BUCKET_DAY: Final = "day"

BUCKET_STEPS: Final[dict[str, str]] = {
    BUCKET_MINUTE: "5 minutes",
    BUCKET_HOUR: "1 hour",
    BUCKET_DAY: "1 day",
}
"""Width of one bucket, as a PostgreSQL interval.

Chosen so each range produces a readable number of points rather than one bar or
several hundred: the last hour becomes twelve five-minute buckets, a day becomes
twenty-four hourly ones, a week seven daily ones.
"""

ALLOWED_BUCKETS: Final[frozenset[str]] = frozenset(BUCKET_STEPS)
"""Time-bucket granularities accepted by the volume aggregation."""

CALENDAR_PREVIEW_LIMIT: Final = 3
"""Run chips previewed inside a calendar day cell."""

DEFAULT_PAGE_SIZE: Final = 60
MAX_PAGE_SIZE: Final = 200
