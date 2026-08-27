"""Automation configuration, read from the environment.

Every setting has a default that works for a local run, so the suite can be
executed by hand with no configuration at all. The runner supplies the rest.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

AUTOMATIONS_ROOT = Path(__file__).resolve().parent.parent.parent
"""Filesystem root of the automation suite."""


def _as_bool(name: str, default: bool) -> bool:
    """Read a boolean environment variable.

    Args:
        name: Environment variable name.
        default: Value returned when unset.

    Returns:
        True for ``1``, ``true``, ``yes`` or ``on``, case-insensitive.
    """
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _as_int(name: str, default: int) -> int:
    """Read an integer environment variable.

    Args:
        name: Environment variable name.
        default: Value returned when unset or empty.

    Returns:
        The parsed integer, or ``default``.
    """
    raw = os.environ.get(name)
    return int(raw) if raw else default


@dataclass(frozen=True)
class AutomationConfig:
    """Settings for one suite execution.

    Attributes:
        target_url: The site under test.
        api_url: NOC API base path, used to report results.
        run_id: Identifier of the run being executed. None when the suite is run
            by hand, in which case nothing is reported.
        worker_id: Identifier recorded against the run.
        headless: Whether to run without a visible browser window.
        slow_mo_ms: Delay between browser actions, for debugging.
        default_timeout_ms: Default element wait timeout.
        navigation_timeout_ms: Default page navigation timeout.
        viewport_width: Browser viewport width.
        viewport_height: Browser viewport height.
        artifacts_dir: Directory receiving screenshots and logs.
        capture_trace: Whether to record a Playwright trace.
    """

    target_url: str
    api_url: str
    run_id: str | None
    worker_id: str
    headless: bool
    slow_mo_ms: int
    default_timeout_ms: int
    navigation_timeout_ms: int
    viewport_width: int
    viewport_height: int
    artifacts_dir: Path
    capture_trace: bool

    @property
    def viewport(self) -> dict[str, int]:
        """Viewport in the shape Playwright expects.

        Returns:
            A mapping with ``width`` and ``height``.
        """
        return {"width": self.viewport_width, "height": self.viewport_height}

    @property
    def reports_to_api(self) -> bool:
        """Whether results should be reported back to the NOC API.

        Returns:
            True when a run id was supplied, meaning the runner started this
            execution. A hand-run suite reports nothing, so experimenting locally
            cannot pollute the dashboard.
        """
        return self.run_id is not None


@lru_cache(maxsize=1)
def get_config() -> AutomationConfig:
    """Build the suite configuration from the environment.

    Cached, so every fixture in a run observes identical settings.

    Returns:
        The populated configuration.
    """
    return AutomationConfig(
        target_url=os.environ.get("AUTOMATION_TARGET_URL", "https://www.google.com"),
        api_url=os.environ.get("NOC_API_URL", "http://localhost:8000/api"),
        run_id=os.environ.get("NOC_RUN_ID") or None,
        worker_id=os.environ.get("NOC_WORKER_ID", "local"),
        headless=_as_bool("AUTOMATION_HEADLESS", True),
        slow_mo_ms=_as_int("AUTOMATION_SLOW_MO", 0),
        default_timeout_ms=_as_int("AUTOMATION_TIMEOUT_MS", 15_000),
        navigation_timeout_ms=_as_int("AUTOMATION_NAV_TIMEOUT_MS", 30_000),
        viewport_width=_as_int("AUTOMATION_VIEWPORT_WIDTH", 1440),
        viewport_height=_as_int("AUTOMATION_VIEWPORT_HEIGHT", 900),
        artifacts_dir=Path(
            os.environ.get("AUTOMATION_ARTIFACTS_DIR", str(AUTOMATIONS_ROOT / "artifacts"))
        ),
        capture_trace=_as_bool("AUTOMATION_TRACE", False),
    )
