"""Liveness and readiness probes.

Two probes rather than one, deliberately. Liveness answers "is the process
alive", so it must not touch the database: a slow query would otherwise get a
healthy container killed. Readiness answers "can it serve traffic", so it does
check dependencies.
"""

from __future__ import annotations

from typing import Any

from flask import Blueprint, Response, jsonify

from config.config import get_config
from database.connection import healthcheck

health_bp = Blueprint("health", __name__)


@health_bp.get("/healthz")
def liveness() -> Response:
    """Report that the process is running.

    Performs no dependency checks, so it stays fast and cannot fail because of a
    slow database.

    Returns:
        HTTP 200 with the service name.
    """
    return jsonify({"status": "ok", "service": get_config().logging.service_name})


@health_bp.get("/readyz")
def readiness() -> tuple[Response, int]:
    """Report whether the process can serve traffic.

    Returns:
        HTTP 200 when the database is reachable, otherwise HTTP 503, with a
        per-dependency breakdown either way.
    """
    database_ready = healthcheck()
    status = 200 if database_ready else 503

    payload: dict[str, Any] = {
        "status": "ready" if database_ready else "degraded",
        "checks": {"database": "up" if database_ready else "down"},
    }
    return jsonify(payload), status
