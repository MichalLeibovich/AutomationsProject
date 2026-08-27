"""Logger factory producing records for the structured JSON formatter."""

from __future__ import annotations

import logging
from typing import Any, MutableMapping


class ContextLogger(logging.LoggerAdapter):
    """Logger adapter injecting component and correlation context."""

    def process(
        self, msg: Any, kwargs: MutableMapping[str, Any]
    ) -> tuple[Any, MutableMapping[str, Any]]:
        """Attach contextual fields to a pending record.

        Values supplied by the caller win, so an explicit ``extra`` still
        overrides the defaults.

        Args:
            msg: The log message.
            kwargs: Keyword arguments for the underlying logger.

        Returns:
            The message and the augmented keyword arguments.
        """
        extra = dict(kwargs.get("extra") or {})
        extra.setdefault("component", self.extra.get("component", "app"))

        correlation_id = _current_correlation_id()
        if correlation_id:
            extra.setdefault("correlation_id", correlation_id)

        kwargs["extra"] = extra
        return msg, kwargs


def _current_correlation_id() -> str | None:
    """Read the correlation identifier for the active request.

    Returns:
        The identifier, or None outside a request. Any failure is swallowed,
        because logging must never raise on a failed context lookup.
    """
    try:
        from flask import g, has_request_context

        if has_request_context():
            value = getattr(g, "correlation_id", None)
            return str(value) if value else None
    except Exception:
        pass
    return None


def get_logger(name: str) -> ContextLogger:
    """Create a logger for a module.

    Only the final dotted segment is used as the component, so
    ``"services.run_service"`` logs as ``"run_service"``. A module run directly
    reports ``__main__``, which is useless as a component, so the entry-point
    file stem is substituted.

    Args:
        name: Module name, normally ``__name__``.

    Returns:
        An adapter populating the component and correlation fields.
    """
    component = name.rsplit(".", maxsplit=1)[-1]

    if component == "__main__":
        import pathlib
        import sys

        main_file = getattr(sys.modules.get("__main__"), "__file__", None)
        component = pathlib.Path(main_file).stem if main_file else "main"

    return ContextLogger(logging.getLogger(name), {"component": component})
