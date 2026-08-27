"""Selectors for the Google home page."""

from __future__ import annotations


class GoogleLocators:
    """Selectors for the search form and results.

    Google renders differently by region and consent state, so each selector is a
    comma-separated list of alternatives: Playwright matches the first that
    resolves. A single brittle selector would fail depending on which variant the
    runner happens to receive.

    Attributes:
        SEARCH_BOX: The query input.
        SEARCH_BUTTON: The submit control, present on the home page only.
        CONSENT_ACCEPT: The cookie-consent accept button, shown in some regions.
        LOGO: The Google wordmark, used as a cheap "page loaded" assertion.
        RESULTS: The results container, present after a search.
    """

    SEARCH_BOX = "textarea[name='q'], input[name='q']"
    SEARCH_BUTTON = "input[name='btnK'], button[type='submit']"
    CONSENT_ACCEPT = "button:has-text('Accept all'), button:has-text('I agree'), #L2AGLb"
    LOGO = "img[alt='Google'], #hplogo, [role='img'][aria-label*='Google']"
    RESULTS = "#search, #rso, div[data-async-context]"
