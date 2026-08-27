"""Shared pytest fixtures and NOC reporting.

Browser launch is session-scoped and everything below it is function-scoped:
starting Chromium costs seconds, so it happens once, while each test gets a fresh
context so state never leaks between tests.

The reporting hooks are what connect this suite to the dashboard. When the runner
starts a test it passes ``NOC_RUN_ID``; the fixtures then claim the run, post the
recorded steps, attach a screenshot on failure, and record the outcome. Run the
suite by hand with no ``NOC_RUN_ID`` and none of that happens, so experimenting
locally cannot pollute the dashboard.
"""

from __future__ import annotations

import sys
import traceback
from pathlib import Path
from typing import Any, Iterator

import pytest
from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright

# The suite runs from its own directory, so its packages import without being
# installed.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.pages.google_home_page import GoogleHomePage  # noqa: E402
from core.utils.artifacts import capture_screenshot  # noqa: E402
from core.utils.config import AutomationConfig, get_config  # noqa: E402
from core.utils.reporter import RunReporter, StepRecorder  # noqa: E402


# ---------------------------------------------------------------------------
# Configuration and browser lifecycle
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def config() -> AutomationConfig:
    """Provide the suite configuration.

    Returns:
        The cached configuration.
    """
    return get_config()


@pytest.fixture(scope="session")
def playwright_instance() -> Iterator[Playwright]:
    """Start and stop Playwright for the session.

    Yields:
        The Playwright driver.
    """
    with sync_playwright() as playwright:
        yield playwright


@pytest.fixture(scope="session")
def browser(playwright_instance: Playwright, config: AutomationConfig) -> Iterator[Browser]:
    """Launch Chromium once for the whole session.

    ``--no-sandbox`` is required to run inside most containers, where the
    sandbox cannot be initialised.

    Args:
        playwright_instance: The Playwright driver.
        config: Suite configuration.

    Yields:
        The launched browser, closed when the session ends.
    """
    # headless=config.headless,
    instance = playwright_instance.chromium.launch(
        headless=False,
        slow_mo=config.slow_mo_ms,
        args=["--no-sandbox", "--disable-dev-shm-usage"],
    )
    yield instance
    instance.close()


@pytest.fixture
def context(browser: Browser, config: AutomationConfig) -> Iterator[BrowserContext]:
    """Create an isolated browser context per test.

    Locale and timezone are pinned so the site under test behaves the same way on
    a developer machine and on a CI runner.

    Args:
        browser: The session browser.
        config: Suite configuration.

    Yields:
        A fresh context, closed when the test ends.
    """
    browser_context = browser.new_context(
        viewport=config.viewport,
        locale="he-IL",
        timezone_id="Asia/Jerusalem",
        ignore_https_errors=True,
    )
    yield browser_context
    browser_context.close()


@pytest.fixture
def page(context: BrowserContext, config: AutomationConfig) -> Iterator[Page]:
    """Open a page with the suite's timeouts applied.

    Args:
        context: The per-test browser context.
        config: Suite configuration.

    Yields:
        The page, closed when the test ends.
    """
    browser_page = context.new_page()
    browser_page.set_default_timeout(config.default_timeout_ms)
    browser_page.set_default_navigation_timeout(config.navigation_timeout_ms)
    yield browser_page
    browser_page.close()


# ---------------------------------------------------------------------------
# Page objects
# ---------------------------------------------------------------------------
@pytest.fixture
def google_page(page: Page, config: AutomationConfig) -> GoogleHomePage:
    """Provide the page object.

    Args:
        page: The test's page.
        config: Suite configuration.

    Returns:
        A page object wrapping it.
    """
    return GoogleHomePage(page, config)


# ---------------------------------------------------------------------------
# NOC reporting
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def reporter(config: AutomationConfig) -> RunReporter:
    """Provide the client that reports results to the NOC API.

    Returns a working object whether or not a run id was supplied; when there is
    none, every method is a no-op, so no test needs to check.

    Args:
        config: Suite configuration.

    Returns:
        The reporter.
    """
    return RunReporter(config)


@pytest.fixture
def step(request: pytest.FixtureRequest, reporter: RunReporter) -> Iterator[StepRecorder]:
    """Record named steps for the dashboard.

    Used as a context manager inside a test::

        with step("פתיחת דף הבית"):
            google_page.open()

    Each block is timed, and an exception inside it is recorded as a failed step
    before propagating — so the debrief names the step that broke rather than
    just the test.

    Args:
        request: The pytest request, used to stash the recorder for the report
            hook.
        reporter: The API reporting client.

    Yields:
        The recorder, called to open a step.
    """
    recorder = StepRecorder()
    request.node.step_recorder = recorder  # type: ignore[attr-defined]

    yield recorder

    reporter.report_steps(recorder.steps)


# ---------------------------------------------------------------------------
# Outcome reporting
# ---------------------------------------------------------------------------
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo) -> Any:
    """Stash each phase's report so the teardown fixture can read the outcome.

    pytest exposes the result only to hooks, not to fixtures, so it is attached
    to the item here.

    Args:
        item: The test that ran.
        call: The phase result.

    Yields:
        Control to the surrounding hook implementations.
    """
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"report_{report.when}", report)


@pytest.fixture(autouse=True)
def report_outcome(
    request: pytest.FixtureRequest,
    reporter: RunReporter,
    config: AutomationConfig,
) -> Iterator[None]:
    """Record the run's outcome, and capture a screenshot when it fails.

    Autouse, so no test has to remember to report. Runs after the test body but
    while the page fixture is still alive, which is what makes the failure
    screenshot possible.

    A failure is described using the first failed step where one exists, because
    "clicked submit — timeout" is far more use in a debrief than a traceback.

    Args:
        request: The pytest request, used to reach the page and the recorder.
        reporter: The API reporting client.
        config: Suite configuration.

    Yields:
        Control to the test.
    """
    reporter.claim()

    yield

    if not config.reports_to_api:
        return

    report = getattr(request.node, "report_call", None) or getattr(
        request.node, "report_setup", None
    )
    passed = report is not None and report.passed

    if passed:
        reporter.complete(status="passed")
        return

    recorder: StepRecorder | None = getattr(request.node, "step_recorder", None)
    failed_step = recorder.failed_step if recorder else None

    # Screenshot before anything else tears down, or the page is gone.
    browser_page = request.node.funcargs.get("page")
    if browser_page is not None:
        path = capture_screenshot(browser_page, config, f"{request.node.name}-failure")
        if path is not None:
            reporter.report_artifact(path)

    reason = (
        f"{failed_step.name}: {failed_step.error_message}"
        if failed_step
        else (str(report.longrepr)[:1000] if report is not None else "הריצה נכשלה")
    )

    reporter.complete(
        status="failed",
        failure_feature=failed_step.name if failed_step else "הרצת האוטומציה",
        failure_error_type=_classify(report),
        failure_reason=reason[:4000],
        stack_trace=str(report.longrepr)[:20_000] if report is not None else None,
    )


def _classify(report: Any) -> str:
    """Map a pytest failure onto one of the dashboard's error categories.

    Keeps the error-type chart meaningful instead of showing one bucket per
    exception class.

    Args:
        report: The failed phase report, or None.

    Returns:
        A Hebrew category label.
    """
    text = str(getattr(report, "longrepr", "")).lower()

    if "timeout" in text or "timed out" in text:
        return "פסק זמן בתגובה"
    if "not found" in text or "no element" in text or "strict mode" in text:
        return "אלמנט לא נמצא"
    if "net::" in text or "connection" in text or "dns" in text:
        return "שגיאת רשת"
    if "assert" in text:
        return "אימות נכשל"
    return "שגיאה כללית"
