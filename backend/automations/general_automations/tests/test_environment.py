"""General environment checks.

These are the automations the dashboard groups under "כללי". They verify the
environment the other automations depend on, so a failure here explains a broad
outage rather than one application's problem.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.general


def test_external_connectivity(google_page, step) -> None:
    """Outbound internet access works from the runner.

    Runs first among the general checks because almost every other automation
    depends on it; a failure here explains the rest.

    Args:
        google_page: Google home page object.
        step: Records named steps for the dashboard.
    """
    with step("פנייה לאתר חיצוני"):
        google_page.open()

    with step("אימות תגובה מהשרת"):
        assert google_page.is_loaded(), "לא התקבלה תגובה מהאתר החיצוני"


def test_page_load_within_budget(google_page, step, config) -> None:
    """The site loads inside the configured navigation budget.

    Slow is treated as a failure rather than ignored: a page that takes twenty
    seconds is broken for an operator even though it eventually renders.

    Args:
        google_page: Google home page object.
        step: Records named steps for the dashboard.
        config: Suite configuration, providing the budget.
    """
    import time

    with step("מדידת זמן טעינה"):
        started = time.perf_counter()
        google_page.open()
        elapsed_ms = int((time.perf_counter() - started) * 1000)

    with step("אימות עמידה בתקציב הזמן"):
        budget = config.navigation_timeout_ms
        assert elapsed_ms < budget, f"הטעינה ארכה {elapsed_ms}ms, מעל התקציב {budget}ms"


def test_consent_banner_is_handled(google_page, step) -> None:
    """The consent banner, if shown, is dismissed rather than blocking the page.

    The banner appears in some regions and not others, so this asserts the page
    is usable afterwards either way.

    Args:
        google_page: Google home page object.
        step: Records named steps for the dashboard.
    """
    with step("פתיחת אתר היעד"):
        google_page.open()

    with step("אימות שהדף שמיש לאחר טיפול בהודעת הסכמה"):
        assert google_page.is_loaded(), "הדף אינו שמיש — ייתכן שהודעת ההסכמה חוסמת"
