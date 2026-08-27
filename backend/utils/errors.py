"""Application exception hierarchy.

Services raise these; the HTTP layer translates them into one response
envelope. That is what keeps business logic free of any Flask dependency.
"""

from __future__ import annotations


class AppError(Exception):
    """Base class for expected, client-visible failures.

    Attributes:
        status_code: HTTP status the API returns.
        code: Stable identifier clients may branch on.
        default_message: Message used when the caller supplies none.
        message: The resolved message.
        details: Optional field-level errors, keyed by field name.
    """

    status_code: int = 500
    code: str = "internal_error"
    default_message: str = "שגיאה בלתי צפויה"

    def __init__(
        self, message: str | None = None, *, details: dict[str, list[str]] | None = None
    ) -> None:
        """Initialise the error.

        Args:
            message: Human-readable message; falls back to the class default.
            details: Field-level errors, keyed by field name.
        """
        self.message = message or self.default_message
        self.details = details
        super().__init__(self.message)


class ValidationError(AppError):
    """Payload or query string failed validation. HTTP 422."""

    status_code = 422
    code = "validation_error"
    default_message = "הנתונים שנשלחו אינם תקינים"


class NotFoundError(AppError):
    """Requested resource does not exist. HTTP 404."""

    status_code = 404
    code = "not_found"
    default_message = "המשאב המבוקש לא נמצא"


class ConflictError(AppError):
    """Request conflicts with current state. HTTP 409."""

    status_code = 409
    code = "conflict"
    default_message = "הפעולה מתנגשת עם המצב הקיים"


class ServiceUnavailableError(AppError):
    """A dependency such as the database is unreachable. HTTP 503."""

    status_code = 503
    code = "service_unavailable"
    default_message = "השירות אינו זמין כרגע"
