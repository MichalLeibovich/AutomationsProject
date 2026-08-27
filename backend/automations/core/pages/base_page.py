"""Shared page behaviour.

Every page object inherits the navigation, waiting and element helpers, so they
are written once. Subclasses add only what is specific to their page.
"""

from __future__ import annotations

from playwright.sync_api import Locator, Page, expect

from core.utils.config import AutomationConfig


class BasePage:
    """Base class for all page objects.

    Attributes:
        page: The Playwright page this object drives.
        config: Suite configuration, providing timeouts and the target URL.
    """

    def __init__(self, page: Page, config: AutomationConfig) -> None:
        """Wrap a Playwright page.

        Args:
            page: The page to drive.
            config: Suite configuration.
        """
        self.page = page
        self.config = config

    # -- navigation --------------------------------------------------------
    def goto(self, url: str) -> None:
        """Navigate to a URL and wait for the document to parse.

        Waits on ``domcontentloaded`` rather than ``load``: a page full of
        third-party assets may never reach ``load``, and the test only needs the
        markup.

        Args:
            url: Absolute URL to open.

        Raises:
            playwright.sync_api.TimeoutError: If navigation does not complete
                within the configured timeout.
        """
        self.page.goto(
            url, wait_until="domcontentloaded", timeout=self.config.navigation_timeout_ms
        )

    # -- elements ----------------------------------------------------------
    def locator(self, selector: str) -> Locator:
        """Resolve a selector to its first match.

        ``.first`` matters: the selectors are comma-separated alternatives, and
        several may resolve at once. Without it Playwright raises on ambiguity.

        Args:
            selector: A selector from the locators package.

        Returns:
            The corresponding locator.
        """
        return self.page.locator(selector).first

    def click(self, selector: str) -> None:
        """Click the first element matching a selector.

        Args:
            selector: A selector from the locators package.

        Raises:
            playwright.sync_api.TimeoutError: If nothing becomes clickable in
                time.
        """
        self.locator(selector).click(timeout=self.config.default_timeout_ms)

    def fill(self, selector: str, value: str) -> None:
        """Replace the value of an input.

        Args:
            selector: A selector from the locators package.
            value: Text to enter.

        Raises:
            playwright.sync_api.TimeoutError: If the field does not appear.
        """
        self.locator(selector).fill(value, timeout=self.config.default_timeout_ms)

    def is_visible(self, selector: str, *, timeout_ms: int | None = None) -> bool:
        """Test whether an element becomes visible.

        Args:
            selector: A selector from the locators package.
            timeout_ms: How long to wait. Defaults to the configured timeout.

        Returns:
            True if it appeared, False if it did not. Returns rather than raising,
            so a caller can branch on an optional element.
        """
        try:
            self.locator(selector).wait_for(
                state="visible", timeout=timeout_ms or self.config.default_timeout_ms
            )
            return True
        except Exception:
            return False

    def wait_for(self, selector: str) -> Locator:
        """Wait for an element to become visible.

        Args:
            selector: A selector from the locators package.

        Returns:
            The locator, so a value can be read straight away.

        Raises:
            playwright.sync_api.TimeoutError: If it does not appear in time.
        """
        element = self.locator(selector)
        element.wait_for(state="visible", timeout=self.config.default_timeout_ms)
        return element

    def expect_visible(self, selector: str) -> None:
        """Assert an element becomes visible.

        Args:
            selector: A selector from the locators package.

        Raises:
            AssertionError: If it does not become visible in time.
        """
        expect(self.locator(selector)).to_be_visible(
            timeout=self.config.default_timeout_ms
        )

    # -- page state --------------------------------------------------------
    @property
    def title(self) -> str:
        """The document title."""
        return self.page.title()

    @property
    def url(self) -> str:
        """The current URL."""
        return self.page.url
