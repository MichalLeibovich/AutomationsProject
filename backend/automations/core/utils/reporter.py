"""Reporting results back to the NOC API.

This is what makes an automation run visible on the dashboard. The suite records
named steps as it goes, then posts them together with the outcome and any
screenshots.

Every method fails soft: a reporting problem must never turn a passing
automation into a failure, so errors are logged and swallowed. The runner is the
backstop — if the suite dies without completing the run, the runner marks it.
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

import requests

from core.utils.config import AutomationConfig


@dataclass
class Step:
    """One recorded step of an automation.

    Attributes:
        index: Zero-based position within the run.
        name: What the step did, in the operator's language.
        status: ``passed``, ``failed`` or ``skipped``.
        duration_ms: How long it took.
        error_message: Failure detail, when it failed.
    """

    index: int
    name: str
    status: str
    duration_ms: int
    error_message: str | None = None

    def to_payload(self) -> dict[str, Any]:
        """Render the step in the API's shape.

        Returns:
            A camelCase mapping ready to post.
        """
        return {
            "index": self.index,
            "name": self.name,
            "status": self.status,
            "durationMs": self.duration_ms,
            "errorMessage": self.error_message,
        }


@dataclass
class StepRecorder:
    """Collects the steps of one test.

    Used through the ``step`` fixture, so timing and failure capture happen
    without each test remembering to do it.

    Attributes:
        steps: Steps recorded so far, in execution order.
    """

    steps: list[Step] = field(default_factory=list)

    @contextmanager
    def __call__(self, name: str) -> Iterator[None]:
        """Record a named step around a block of test code.

        The step is timed, and an exception inside the block is recorded as a
        failure before being re-raised — so the report says which step broke, not
        merely that the test did.

        Args:
            name: What the step does, in the operator's language. This text ends
                up on the dashboard, so it should read as an action.

        Yields:
            Control to the block being measured.

        Raises:
            Exception: Whatever the block raised, after recording it.
        """
        started = time.perf_counter()
        index = len(self.steps)

        try:
            yield
        except Exception as error:
            self.steps.append(
                Step(
                    index=index,
                    name=name,
                    status="failed",
                    duration_ms=int((time.perf_counter() - started) * 1000),
                    error_message=f"{type(error).__name__}: {error}"[:4000],
                )
            )
            raise
        else:
            self.steps.append(
                Step(
                    index=index,
                    name=name,
                    status="passed",
                    duration_ms=int((time.perf_counter() - started) * 1000),
                )
            )

    @property
    def failed_step(self) -> Step | None:
        """The first step that failed.

        Returns:
            The step, or None when every step passed. Used to describe the
            failure without parsing a traceback.
        """
        return next((step for step in self.steps if step.status == "failed"), None)


class RunReporter:
    """Posts steps, artifacts and the final outcome to the NOC API.

    Attributes:
        config: Suite configuration, providing the API address and run id.
    """

    def __init__(self, config: AutomationConfig) -> None:
        """Initialise the reporter.

        Args:
            config: Suite configuration.
        """
        self.config = config
        self._session = requests.Session()

    @property
    def _run_path(self) -> str:
        """Base path of the run being reported on."""
        return f"{self.config.api_url}/runs/{self.config.run_id}"

    def claim(self) -> None:
        """Mark the run as running.

        Called once the browser is up, so the dashboard shows the automation as
        in flight rather than queued.
        """
        if not self.config.reports_to_api:
            return

        self._post(f"{self._run_path}/claim", {"workerId": self.config.worker_id})

    def report_steps(self, steps: list[Step]) -> None:
        """Post the recorded steps as one batch.

        Batched rather than one request per step, so a ten-step automation costs
        one round trip instead of ten.

        Args:
            steps: The steps to report. An empty list is ignored.
        """
        if not self.config.reports_to_api or not steps:
            return

        self._post(
            f"{self._run_path}/steps", {"steps": [step.to_payload() for step in steps]}
        )

    def report_artifact(self, path: Path, kind: str = "screenshot") -> None:
        """Record a file the automation produced.

        Only metadata is sent; the file itself stays on disk where the API can
        serve it from.

        Args:
            path: Path to the written file.
            kind: screenshot, log, trace, video, har or report.
        """
        if not self.config.reports_to_api or not path.is_file():
            return

        self._post(
            f"{self._run_path}/artifacts",
            {
                "kind": kind,
                "fileName": path.name,
                "localPath": str(path.resolve()),
                "contentType": "image/png" if path.suffix == ".png" else "text/plain",
                "sizeBytes": path.stat().st_size,
            },
        )

    def complete(
        self,
        *,
        status: str,
        failure_feature: str | None = None,
        failure_error_type: str | None = None,
        failure_reason: str | None = None,
        stack_trace: str | None = None,
    ) -> None:
        """Record the run's outcome.

        Args:
            status: ``passed``, ``failed``, ``timed_out`` or ``cancelled``.
            failure_feature: Which part failed, for the dashboard breakdown.
            failure_error_type: Failure category, for the error-type chart.
            failure_reason: Human-readable explanation. Mandatory for a failure —
                the API rejects a failure without one, because a debrief with no
                reason is unusable.
            stack_trace: Full traceback, when one was captured.
        """
        if not self.config.reports_to_api:
            return

        self._post(
            f"{self._run_path}/complete",
            {
                "status": status,
                "failureFeature": failure_feature,
                "failureErrorType": failure_error_type,
                "failureReason": failure_reason,
                "stackTrace": stack_trace,
            },
        )

    def _post(self, url: str, payload: dict[str, Any]) -> None:
        """Send one request, swallowing any failure.

        Reporting must never break the automation it is reporting on, so a
        network problem prints a warning rather than raising.

        Args:
            url: Absolute URL to post to.
            payload: JSON body.
        """
        try:
            response = self._session.post(url, json=payload, timeout=10)
            if response.status_code >= 400:
                print(f"[reporter] {url} → {response.status_code} {response.text[:200]}")
        except Exception as error:
            print(f"[reporter] failed to reach {url}: {error}")
