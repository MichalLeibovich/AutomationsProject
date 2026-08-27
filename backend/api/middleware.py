"""Request middleware and request-scoped accessors.

The error handlers registered here translate the :class:`~utils.errors.AppError`
hierarchy into a single response envelope::

    {"error": {"code": ..., "message": ..., "details": ..., "correlationId": ...}}

One shape means the frontend has one thing to parse, and an unexpected fault
never leaks a schema detail or file path to the client.
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Final

from flask import Flask, Response, g, jsonify, request

from utils.errors import AppError
from utils.logger import get_logger

logger = get_logger(__name__)

CORRELATION_HEADER: Final = "X-Correlation-Id"
"""Header carrying the request correlation identifier, in both directions."""

_QUIET_PATHS: Final[frozenset[str]] = frozenset({"/healthz", "/readyz"})
"""Paths excluded from request logging, so probes do not dominate log volume."""


def register_middleware(app: Flask) -> None:
    """Attach request hooks and error handlers to an application.

    Installs correlation-identifier propagation, request timing, and handlers for
    the application error hierarchy, unmatched routes and unexpected exceptions.

    Args:
        app: The Flask application to configure.
    """

    @app.before_request
    def _start_request() -> None:
        """Establish the correlation identifier and start the request timer.

        A client-supplied identifier is reused so one action can be traced end to
        end; otherwise a new one is minted.
        """
        g.correlation_id = request.headers.get(CORRELATION_HEADER) or str(uuid.uuid4())
        g.request_started = time.perf_counter()

    @app.after_request
    def _finish_request(response: Response) -> Response:
        """Echo the correlation identifier and log the completed request.

        Args:
            response: The outgoing response.

        Returns:
            The same response, with the correlation header set.
        """
        response.headers[CORRELATION_HEADER] = getattr(g, "correlation_id", "unknown")

        started = getattr(g, "request_started", None)
        if started is not None and request.path not in _QUIET_PATHS:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            logger.info(
                "%s %s %s",
                request.method,
                request.path,
                response.status_code,
                extra={"duration_ms": duration_ms, "status": response.status_code},
            )

        return response

    @app.errorhandler(AppError)
    def _handle_app_error(error: AppError) -> tuple[Response, int]:
        """Render an expected application error as the standard envelope.

        Args:
            error: The raised application error.

        Returns:
            The JSON response and the error's HTTP status.
        """
        payload: dict[str, Any] = {
            "error": {
                "code": error.code,
                "message": error.message,
                "correlationId": getattr(g, "correlation_id", "unknown"),
            }
        }
        if error.details:
            payload["error"]["details"] = error.details

        if error.status_code >= 500:
            logger.error("application error: %s", error.message, extra={"code": error.code})
        else:
            logger.info("client error: %s", error.message, extra={"code": error.code})

        return jsonify(payload), error.status_code

    @app.errorhandler(404)
    def _handle_not_found(_error: Any) -> tuple[Response, int]:
        """Render an unmatched route in the standard envelope.

        Args:
            _error: The Werkzeug exception, unused.

        Returns:
            The JSON response and HTTP 404.
        """
        return (
            jsonify(
                {
                    "error": {
                        "code": "not_found",
                        "message": "הנתיב המבוקש אינו קיים",
                        "correlationId": getattr(g, "correlation_id", "unknown"),
                    }
                }
            ),
            404,
        )

    @app.errorhandler(Exception)
    def _handle_unexpected(error: Exception) -> tuple[Response, int]:
        """Render an unexpected fault without disclosing internals.

        The stack trace goes to the logs; the client receives a generic message,
        so an internal fault never leaks schema details or file paths.

        Args:
            error: The unhandled exception.

        Returns:
            The JSON response and HTTP 500.
        """
        logger.exception("unhandled exception: %s", error)
        return (
            jsonify(
                {
                    "error": {
                        "code": "internal_error",
                        "message": "שגיאה בלתי צפויה בשרת",
                        "correlationId": getattr(g, "correlation_id", "unknown"),
                    }
                }
            ),
            500,
        )


def correlation_id() -> str:
    """Return this request's correlation identifier.

    Returns:
        The identifier, or ``"unknown"`` outside a request.
    """
    return str(getattr(g, "correlation_id", "unknown"))


def json_body() -> dict[str, Any]:
    """Parse the request body as a JSON object.

    Returns:
        The decoded object, or an empty mapping when the body is absent,
        malformed or not an object. Validators therefore always receive a
        consistent mapping and report a missing field rather than crashing.
    """
    body = request.get_json(silent=True)
    return body if isinstance(body, dict) else {}
