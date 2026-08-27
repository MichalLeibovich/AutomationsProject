"""Request validation.

Written without a schema library so the rules sit in one readable place and
raise the application's own :class:`ValidationError`. Every validator returns a
cleaned value rather than mutating its input, and every message is user-facing
Hebrew.
"""

from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime
from typing import Any, Final, Iterable, Mapping, NoReturn

from utils.constants import (
    ALL_STATUSES,
    ALL_TRIGGER_SOURCES,
    ARTIFACT_KINDS,
    MAX_PAGE_SIZE,
    SORT_DIRECTIONS,
    SORTABLE_RUN_COLUMNS,
    STEP_STATUSES,
    TERMINAL_STATUSES,
)
from utils.errors import ValidationError

_HEX_COLOR_RE: Final[re.Pattern[str]] = re.compile(r"^#[0-9A-Fa-f]{6}$")
_SLUG_RE: Final[re.Pattern[str]] = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _fail(field: str, message: str) -> NoReturn:
    """Raise a field-scoped validation error.

    Args:
        field: Offending field name, as the client sent it.
        message: Hebrew description of the problem.

    Raises:
        ValidationError: Always.
    """
    raise ValidationError(details={field: [message]})


# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------
def require_uuid(value: Any, field: str) -> uuid.UUID:
    """Validate that a value is a UUID.

    Args:
        value: Candidate value, typically from a URL path.
        field: Field name used in the error details.

    Returns:
        The parsed UUID.

    Raises:
        ValidationError: If it is not a well-formed UUID.
    """
    try:
        return uuid.UUID(str(value))
    except (ValueError, AttributeError, TypeError):
        _fail(field, "מזהה אינו תקין")


def require_string(
    value: Any, field: str, *, min_length: int = 1, max_length: int = 255
) -> str:
    """Validate a mandatory string and strip surrounding whitespace.

    Args:
        value: Candidate value.
        field: Field name used in the error details.
        min_length: Minimum length after stripping.
        max_length: Maximum length after stripping.

    Returns:
        The stripped string.

    Raises:
        ValidationError: If it is not a string of valid length.
    """
    if not isinstance(value, str):
        _fail(field, "נדרש טקסט")
    cleaned = value.strip()
    if len(cleaned) < min_length:
        _fail(field, f"נדרשים לפחות {min_length} תווים")
    if len(cleaned) > max_length:
        _fail(field, f"עד {max_length} תווים")
    return cleaned


def optional_string(value: Any, field: str, *, max_length: int = 255) -> str | None:
    """Validate an optional string.

    Args:
        value: Candidate value.
        field: Field name used in the error details.
        max_length: Maximum length after stripping.

    Returns:
        The stripped string, or None when absent or empty.

    Raises:
        ValidationError: If a non-empty value is not a valid string.
    """
    if value is None or value == "":
        return None
    return require_string(value, field, max_length=max_length)


def require_hex_color(value: Any, field: str = "color") -> str:
    """Validate a six-digit hex colour and uppercase it.

    Args:
        value: Candidate value in ``#RRGGBB`` form.
        field: Field name used in the error details.

    Returns:
        The uppercased colour.

    Raises:
        ValidationError: If it is not a six-digit hex colour.
    """
    color = require_string(value, field, min_length=7, max_length=7)
    if not _HEX_COLOR_RE.match(color):
        _fail(field, "נדרש צבע בפורמט #RRGGBB")
    return color.upper()


def require_slug(value: Any, field: str = "slug") -> str:
    """Validate a URL slug and lowercase it.

    Args:
        value: Candidate value.
        field: Field name used in the error details.

    Returns:
        The lowercased slug.

    Raises:
        ValidationError: If it contains anything but lowercase letters, digits
            and single interior hyphens.
    """
    slug = require_string(value, field, max_length=64).lower()
    if not _SLUG_RE.match(slug):
        _fail(field, "נדרשות אותיות קטנות, ספרות ומקפים בלבד")
    return slug


def require_choice(value: Any, field: str, allowed: Iterable[str]) -> str:
    """Validate that a value is one of a fixed set.

    Args:
        value: Candidate value.
        field: Field name used in the error details.
        allowed: Permitted values.

    Returns:
        The value as a string.

    Raises:
        ValidationError: If it is not permitted.
    """
    options = tuple(allowed)
    if value not in options:
        _fail(field, f"נדרש אחד מהערכים: {', '.join(options)}")
    return str(value)


def optional_choice(
    value: Any, field: str, allowed: Iterable[str], *, default: str | None = None
) -> str | None:
    """Validate an optional value against a fixed set.

    Args:
        value: Candidate value.
        field: Field name used in the error details.
        allowed: Permitted values.
        default: Returned when absent or empty.

    Returns:
        The value as a string, or ``default``.

    Raises:
        ValidationError: If a non-empty value is not permitted.
    """
    if value is None or value == "":
        return default
    return require_choice(value, field, allowed)


def parse_int(value: Any, field: str, *, default: int, minimum: int, maximum: int) -> int:
    """Validate an optional bounded integer.

    Args:
        value: Candidate value.
        field: Field name used in the error details.
        default: Returned when absent or empty.
        minimum: Smallest permitted value, inclusive.
        maximum: Largest permitted value, inclusive.

    Returns:
        The parsed integer, or ``default``.

    Raises:
        ValidationError: If it is not an integer, or is out of range.
    """
    if value is None or value == "":
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        _fail(field, "נדרש מספר שלם")
    if parsed < minimum or parsed > maximum:
        _fail(field, f"נדרש ערך בין {minimum} ל-{maximum}")
    return parsed


def parse_bool(value: Any, *, default: bool = False) -> bool:
    """Coerce a value to a boolean.

    Args:
        value: Candidate value.
        default: Returned when the value is None.

    Returns:
        True for ``1``, ``true``, ``yes`` or ``on``, case-insensitive.
    """
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def parse_datetime(value: Any, field: str) -> datetime | None:
    """Validate an optional ISO 8601 timestamp.

    A trailing ``Z`` is accepted and treated as UTC.

    Args:
        value: Candidate value.
        field: Field name used in the error details.

    Returns:
        The parsed datetime, or None when absent or empty.

    Raises:
        ValidationError: If a non-empty value is not valid ISO 8601.
    """
    if value is None or value == "":
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        _fail(field, "נדרש תאריך בפורמט ISO 8601")


# ---------------------------------------------------------------------------
# Composite validators
# ---------------------------------------------------------------------------
def validate_run_list_query(args: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the query string for the paged run list.

    Sort inputs resolve through whitelists, so a request value maps to a known
    column identifier rather than reaching the query text.

    Args:
        args: Query parameters, or a JSON body for the export endpoint.

    Returns:
        Keyword arguments for the run listing.

    Raises:
        ValidationError: If any parameter is malformed or out of range.
    """
    return {
        "scope": optional_string(args.get("scope"), "scope", max_length=120),
        "status": optional_choice(
            args.get("status"), "status", (*ALL_STATUSES, "all"), default="all"
        ),
        "search": optional_string(args.get("search"), "search", max_length=200),
        "date_from": parse_datetime(args.get("from"), "from"),
        "date_to": parse_datetime(args.get("to"), "to"),
        "sort": optional_choice(
            args.get("sort"), "sort", SORTABLE_RUN_COLUMNS.keys(), default="started_at"
        ),
        "direction": optional_choice(
            args.get("direction"), "direction", SORT_DIRECTIONS.keys(), default="desc"
        ),
        "limit": parse_int(
            args.get("limit"), "limit", default=60, minimum=1, maximum=MAX_PAGE_SIZE
        ),
        "offset": parse_int(
            args.get("offset"), "offset", default=0, minimum=0, maximum=1_000_000
        ),
    }


def validate_start_run_body(body: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the body for triggering one run.

    Args:
        body: JSON body with ``testDefinitionId`` and ``idempotencyKey``, plus
            optional ``triggeredBy`` and ``triggerSource``.

    Returns:
        Keyword arguments for the run service.

    Raises:
        ValidationError: If a required field is missing or malformed.
    """
    return {
        "test_definition_id": require_uuid(body.get("testDefinitionId"), "testDefinitionId"),
        "idempotency_key": require_string(
            body.get("idempotencyKey"), "idempotencyKey", min_length=8, max_length=64
        ),
        "triggered_by": optional_string(body.get("triggeredBy"), "triggeredBy", max_length=120)
        or "manual",
        "trigger_source": optional_choice(
            body.get("triggerSource"), "triggerSource", ALL_TRIGGER_SOURCES, default="manual"
        ),
    }


def validate_bulk_run_body(body: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the body for a bulk main-test run.

    Args:
        body: JSON body with optional ``scope`` and ``triggeredBy``, plus a
            mandatory ``idempotencyKey``.

    Returns:
        Keyword arguments for the run service. A ``scope`` of ``"general"``
        passes validation here and is rejected by the service, where the rule
        belongs.

    Raises:
        ValidationError: If a field is malformed.
    """
    return {
        "scope": optional_string(body.get("scope"), "scope", max_length=120),
        "idempotency_key": require_string(
            body.get("idempotencyKey"), "idempotencyKey", min_length=8, max_length=64
        ),
        "triggered_by": optional_string(body.get("triggeredBy"), "triggeredBy", max_length=120)
        or "manual",
    }


def validate_complete_run_body(body: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the body a runner posts when a run finishes.

    Args:
        body: JSON body with ``status`` and optional failure detail and counts.

    Returns:
        Keyword arguments for the run service.

    Raises:
        ValidationError: If the status is not terminal, or a reported failure
            carries no reason.
    """
    status = require_choice(body.get("status"), "status", sorted(TERMINAL_STATUSES))
    reason = optional_string(body.get("failureReason"), "failureReason", max_length=4000)

    if status == "failed" and not reason:
        _fail("failureReason", "ריצה שנכשלה מחייבת תיאור כשל")

    return {
        "status": status,
        "failure_feature": optional_string(
            body.get("failureFeature"), "failureFeature", max_length=200
        ),
        "failure_error_type": optional_string(
            body.get("failureErrorType"), "failureErrorType", max_length=200
        ),
        "failure_reason": reason,
        "stack_trace": optional_string(body.get("stackTrace"), "stackTrace", max_length=20_000),
    }


def validate_steps_body(body: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Validate a batch of run steps.

    Steps are posted as one batch rather than one request each, so a run with
    twenty steps costs one round trip.

    Args:
        body: JSON body with a ``steps`` array.

    Returns:
        The cleaned steps, in the order given.

    Raises:
        ValidationError: If ``steps`` is absent, empty, over 500 entries, or any
            entry is malformed.
    """
    steps = body.get("steps")
    if not isinstance(steps, list) or not steps:
        _fail("steps", "נדרשת רשימת שלבים")
    if len(steps) > 500:
        _fail("steps", "עד 500 שלבים בבקשה אחת")

    cleaned: list[dict[str, Any]] = []
    for index, step in enumerate(steps):
        if not isinstance(step, dict):
            _fail("steps", f"שלב {index} אינו תקין")
        cleaned.append(
            {
                "step_index": parse_int(
                    step.get("index"), "steps", default=index, minimum=0, maximum=10_000
                ),
                "name": require_string(step.get("name"), "steps", max_length=300),
                "status": require_choice(step.get("status"), "steps", STEP_STATUSES),
                "duration_ms": parse_int(
                    step.get("durationMs"), "steps", default=0, minimum=0, maximum=86_400_000
                ),
                "error_message": optional_string(
                    step.get("errorMessage"), "steps", max_length=4000
                ),
            }
        )
    return cleaned


def validate_artifact_body(body: Mapping[str, Any]) -> dict[str, Any]:
    """Validate artifact metadata posted by a runner.

    Args:
        body: JSON body describing one stored file.

    Returns:
        Keyword arguments for the run service.

    Raises:
        ValidationError: If required fields are missing, or neither a local path
            nor an object key is supplied — an artifact nobody can locate is not
            an artifact.
    """
    local_path = optional_string(body.get("localPath"), "localPath", max_length=1000)
    s3_key = optional_string(body.get("s3Key"), "s3Key", max_length=1000)

    if not local_path and not s3_key:
        _fail("localPath", "נדרש נתיב מקומי או מפתח אחסון")

    return {
        "kind": require_choice(body.get("kind"), "kind", ARTIFACT_KINDS),
        "file_name": require_string(body.get("fileName"), "fileName", max_length=300),
        "local_path": local_path,
        "s3_bucket": optional_string(body.get("s3Bucket"), "s3Bucket", max_length=200),
        "s3_key": s3_key,
        "content_type": optional_string(body.get("contentType"), "contentType", max_length=120)
        or "application/octet-stream",
        "size_bytes": parse_int(
            body.get("sizeBytes"), "sizeBytes", default=0, minimum=0, maximum=10_000_000_000
        ),
    }


def validate_comment_body(body: Mapping[str, Any]) -> dict[str, str]:
    """Validate a run comment.

    Args:
        body: JSON body with ``body`` and optional ``authorName``.

    Returns:
        The cleaned comment text and author name.

    Raises:
        ValidationError: If the text is missing, empty or over 4000 characters.
    """
    return {
        "body": require_string(body.get("body"), "body", min_length=1, max_length=4000),
        "author_name": optional_string(body.get("authorName"), "authorName", max_length=120)
        or "אנונימי",
    }


def validate_dashboard_query(args: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the dashboard query string.

    Args:
        args: Query parameters ``scope``, ``range``, ``from`` and ``to``.

    Returns:
        Keyword arguments for the analytics service.

    Raises:
        ValidationError: If any parameter is malformed.
    """
    date_from = parse_datetime(args.get("from"), "from")
    date_to = parse_datetime(args.get("to"), "to")

    # Checked here as well as in the interface: the browser's date picker can be
    # bypassed by typing, and by anything calling the API directly. An inverted
    # range would otherwise return an empty chart rather than an explanation.
    if date_from and date_to and date_from > date_to:
        _fail("from", "תאריך ההתחלה חייב להיות לפני תאריך הסיום")

    # A bare date such as "2026-08-01" parses without a timezone, so it cannot be
    # compared against an aware "now" directly. Naive values are read as UTC.
    now = datetime.now(UTC)
    for field, value in (("from", date_from), ("to", date_to)):
        if value is None:
            continue
        aware = value if value.tzinfo is not None else value.replace(tzinfo=UTC)
        if aware > now:
            _fail(field, "לא ניתן לבחור תאריך עתידי")

    return {
        "scope": optional_string(args.get("scope"), "scope", max_length=120),
        "range": optional_choice(
            args.get("range"), "range", ("hour", "day", "week", "custom"), default="week"
        ),
        "date_from": date_from,
        "date_to": date_to,
    }


def validate_calendar_query(args: Mapping[str, Any]) -> dict[str, int]:
    """Validate the calendar query string.

    Args:
        args: Query parameters ``year`` and ``month``.

    Returns:
        The year and month. Both default to 0, which the route reads as the
        current year and month.

    Raises:
        ValidationError: If either value is non-numeric or out of range.
    """
    return {
        "year": parse_int(args.get("year"), "year", default=0, minimum=2000, maximum=2100),
        "month": parse_int(args.get("month"), "month", default=0, minimum=1, maximum=12),
    }


def validate_application_body(body: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the body for creating an application.

    Args:
        body: JSON body with ``name``, ``slug``, ``color`` and optional
            ``displayOrder``.

    Returns:
        Keyword arguments for the catalog service.

    Raises:
        ValidationError: If any field is missing or malformed.
    """
    return {
        "name": require_string(body.get("name"), "name", max_length=120),
        "slug": require_slug(body.get("slug")),
        "color": require_hex_color(body.get("color")),
        "display_order": parse_int(
            body.get("displayOrder"), "displayOrder", default=0, minimum=0, maximum=999
        ),
    }


def validate_definition_body(body: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the body for creating a test definition.

    Args:
        body: JSON body describing the automation, including its
            ``runnerTarget`` — the pytest node id that ties the row to a test on
            disk.

    Returns:
        Keyword arguments for the catalog service.

    Raises:
        ValidationError: If any field is missing or malformed.
    """
    application_id_raw = body.get("applicationId")

    return {
        "application_id": (
            require_uuid(application_id_raw, "applicationId") if application_id_raw else None
        ),
        "scope": require_choice(body.get("scope"), "scope", ("application", "general")),
        "kind": require_choice(body.get("kind"), "kind", ("main", "secondary", "general")),
        "name": require_string(body.get("name"), "name", max_length=200),
        "description": optional_string(body.get("description"), "description", max_length=2000),
        "runner_target": require_string(body.get("runnerTarget"), "runnerTarget", max_length=300),
        "display_order": parse_int(
            body.get("displayOrder"), "displayOrder", default=0, minimum=0, maximum=999
        ),
        "timeout_seconds": parse_int(
            body.get("timeoutSeconds"), "timeoutSeconds", default=600, minimum=10, maximum=7200
        ),
    }
