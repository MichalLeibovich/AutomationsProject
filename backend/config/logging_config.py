"""Structured JSON logging.

Every record is one JSON object in a fixed shape::

    {"component": ..., "service": ..., "level": ..., "severity": ...,
     "timestamp": ..., "message": ...}

``level`` carries the name and ``severity`` the numeric value, so records are
readable by people and sortable by machines.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any, Final

from config.config import get_config

_RESERVED: Final[frozenset[str]] = frozenset(
    {
        "args", "asctime", "created", "exc_info", "exc_text", "filename",
        "funcName", "levelname", "levelno", "lineno", "module", "msecs",
        "message", "msg", "name", "pathname", "process", "processName",
        "relativeCreated", "stack_info", "stacklevel", "thread", "threadName",
        "taskName",
    }
)
"""Standard LogRecord attributes.

Anything outside this set is caller-supplied context and is nested under
``context`` in the emitted record.
"""


class JsonFormatter(logging.Formatter):
    """Formats records as single-line JSON in the agreed schema."""

    def __init__(self, service_name: str) -> None:
        """Initialise the formatter.

        Args:
            service_name: Deployable name emitted in the ``service`` field.
        """
        super().__init__()
        self._service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        """Render a record as JSON.

        Args:
            record: The record to format.

        Returns:
            A single-line JSON document. Non-ASCII is preserved rather than
            escaped, keeping Hebrew messages readable.
        """
        payload: dict[str, Any] = {
            "component": getattr(record, "component", record.name),
            "service": getattr(record, "service", self._service_name),
            "level": record.levelname,
            "severity": record.levelno,
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(
                timespec="milliseconds"
            ),
            "message": record.getMessage(),
        }

        correlation_id = getattr(record, "correlation_id", None)
        if correlation_id:
            payload["correlationId"] = str(correlation_id)

        extras = {
            key: value
            for key, value in record.__dict__.items()
            if key not in _RESERVED
            and key not in {"component", "service", "correlation_id"}
            and not key.startswith("_")
        }
        if extras:
            payload["context"] = extras

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging() -> None:
    """Install the JSON formatter on the root logger.

    Called once at startup. Existing handlers are discarded so the process
    cannot emit a mixture of formats. Werkzeug's access log is quietened because
    request logging is done by the middleware, which also records timing.
    """
    config = get_config()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter(config.logging.service_name))

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(config.logging.level)

    logging.getLogger("werkzeug").setLevel(logging.WARNING)
