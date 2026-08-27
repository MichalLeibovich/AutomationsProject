"""Google home page object.

Shared by every application's automations. Each application folder points at it
rather than defining its own copy, so a change to how Google renders is one edit.
"""

from __future__ import annotations

from playwright.sync_api import Page

from core.locators.google_locators import GoogleLocators
from core.pages.base_page import BasePage
from core.utils.config import AutomationConfig


class GoogleHomePage(BasePage):
    """Drives the Google home page: opening it, searching, reading results."""

    def __init__(self, page: Page, config: AutomationConfig) -> None:
        """Wrap a page and remember the configured target URL.

        Args:
            page: The page to drive.
            config: Suite configuration.
        """
        super().__init__(page, config)
        self.url_under_test = config.target_url

    def open(self) -> "GoogleHomePage":
        """Open the site and dismiss the consent banner if one appears.

        Returns:
            This object, for chaining.

        Raises:
            playwright.sync_api.TimeoutError: If the page does not load.
        """
        self.goto(self.url_under_test)
        self.accept_consent_if_present()
        return self

    def accept_consent_if_present(self) -> bool:
        """Accept the cookie banner when the region shows one.

        Handled rather than assumed absent: the banner appears in some regions and
        not others, and it covers the search box when it does.

        Returns:
            True if a banner was dismissed, False if none appeared.
        """
        if self.is_visible(GoogleLocators.CONSENT_ACCEPT, timeout_ms=3_000):
            self.click(GoogleLocators.CONSENT_ACCEPT)
            return True
        return False

    def is_loaded(self) -> bool:
        """Test whether the home page rendered.

        Returns:
            True when the search box is present. The search box rather than the
            logo, because it is what the page is actually for.
        """
        return self.is_visible(GoogleLocators.SEARCH_BOX)

    def is_logo_visible(self) -> bool:
        """Test whether the Google wordmark rendered.

        Returns:
            True if present. Optional in some layouts, so failing this is not
            treated as a page failure.
        """
        return self.is_visible(GoogleLocators.LOGO, timeout_ms=5_000)

    def search(self, query: str) -> "GoogleHomePage":
        """Type a query and submit it.

        Submits with Enter rather than clicking the button: the button is not
        present on every variant of the page, whereas Enter always works.

        Args:
            query: The text to search for.

        Returns:
            This object, for chaining.

        Raises:
            playwright.sync_api.TimeoutError: If the search box never appears.
        """
        self.fill(GoogleLocators.SEARCH_BOX, query)
        self.locator(GoogleLocators.SEARCH_BOX).press("Enter")
        return self

    def has_results(self) -> bool:
        """Test whether a results list rendered.

        Returns:
            True when the results container appears.
        """
        return self.is_visible(GoogleLocators.RESULTS)
