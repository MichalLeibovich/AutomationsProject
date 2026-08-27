"""Screenshot capture.

Files are written into a per-run folder, so artifacts from concurrent runs cannot
collide and a whole run's evidence can be removed in one delete.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Final

from playwright.sync_api import Page

from core.utils.config import AutomationConfig

_UNSAFE: Final[re.Pattern[str]] = re.compile(r"[^A-Za-z0-9._-]+")


def slugify(value: str) -> str:
    """Reduce a string to a filesystem-safe fragment.

    Args:
        value: Arbitrary text, typically a test name.

    Returns:
        The value with unsafe runs collapsed to hyphens, trimmed to 100
        characters. Returns ``"unnamed"`` if nothing usable remains.
    """
    return _UNSAFE.sub("-", value).strip("-")[:100] or "unnamed"


def run_artifact_dir(config: AutomationConfig) -> Path:
    """Resolve, and create, the folder for this run's artifacts.

    Args:
        config: Suite configuration.

    Returns:
        The directory. Named for the run when one exists, otherwise for the
        current time, so hand-run executions still land somewhere sensible.
    """
    name = config.run_id or f"local-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    directory = config.artifacts_dir / name
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def capture_screenshot(page: Page, config: AutomationConfig, label: str) -> Path | None:
    """Write a full-page screenshot.

    Args:
        page: The page to capture.
        config: Suite configuration.
        label: Label incorporated into the file name.

    Returns:
        The path written, or None if the page could not be captured — a crashed
        page must not mask the original test failure.
    """
    try:
        path = run_artifact_dir(config) / f"{slugify(label)}.png"
        page.screenshot(path=str(path), full_page=True)
        return path
    except Exception as error:
        print(f"[artifacts] screenshot failed: {error}")
        return None
