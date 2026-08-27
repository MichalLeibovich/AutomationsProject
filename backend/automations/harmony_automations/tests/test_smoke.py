"""Main automation for הרמוניה — the one an operator runs by reflex.

Opens the site under test and verifies it is usable. Deliberately shallow: a
main test that takes a minute is a main test nobody runs.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.smoke


def test_site_is_reachable(google_page, step) -> None:
    """The site loads and presents a usable search box.

    Args:
        google_page: Google home page object.
        step: Records named steps for the dashboard.
    """
    with step("פתיחת אתר היעד"):
        google_page.open()

    with step("אימות טעינת הדף"):
        assert google_page.is_loaded(), "תיבת החיפוש לא נטענה"

    with step("אימות כותרת הדף"):
        assert google_page.title, "לדף אין כותרת"


def test_search_returns_results(google_page, step) -> None:
    """A search returns a results list.

    Args:
        google_page: Google home page object.
        step: Records named steps for the dashboard.
    """
    with step("פתיחת אתר היעד"):
        google_page.open()

    with step("ביצוע חיפוש"):
        google_page.search("הרמוניה")

    with step("אימות תוצאות"):
        assert google_page.has_results(), "לא הוצגו תוצאות חיפוש"
