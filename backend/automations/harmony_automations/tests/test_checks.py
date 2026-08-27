"""Secondary automations for הרמוניה.

Run less often than the main test and check narrower things.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.regression


def test_logo_is_displayed(google_page, step) -> None:
    """The site's wordmark renders.

    Args:
        google_page: Google home page object.
        step: Records named steps for the dashboard.
    """
    with step("פתיחת אתר היעד"):
        google_page.open()

    with step("אימות הצגת הלוגו"):
        assert google_page.is_logo_visible(), "הלוגו לא הוצג"


def test_page_url_is_correct(google_page, step) -> None:
    """The browser lands on the address that was requested.

    Guards against a redirect quietly sending the automation somewhere else.

    Args:
        google_page: Google home page object.
        step: Records named steps for the dashboard.
    """
    with step("פתיחת אתר היעד"):
        google_page.open()

    with step("אימות כתובת הדף"):
        assert "google" in google_page.url.lower(), f"כתובת בלתי צפויה: {google_page.url}"
