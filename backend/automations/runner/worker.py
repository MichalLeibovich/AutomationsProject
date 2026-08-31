"""Polling worker that executes queued automation runs.

Usage::

    python -m runner.worker
    python -m runner.worker --once            # drain the queue and exit
    python -m runner.worker --run-id <UUID>   # execute one specific run

Design notes worth knowing:

* **Polling, not a queue broker.** At the volume this system handles, a two-second
  poll against an indexed column costs less operationally than running RabbitMQ
  or Redis alongside it.
* **pytest runs in a subprocess.** A test that hangs, segfaults or calls
  ``sys.exit`` cannot take the worker down with it, and the timeout is
  enforceable.
* **The suite reports its own results**, via ``NOC_RUN_ID`` in the child's
  environment. The worker only reports what the suite could not — a crash before
  reporting, or a timeout.
"""

from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import requests

AUTOMATIONS_ROOT = Path(__file__).resolve().parent.parent
"""Filesystem root of the automation suite."""

POLL_INTERVAL_SECONDS = 2
"""Seconds between polls when the queue is empty."""

TICK_INTERVAL_SECONDS = 60
"""Seconds between scheduler ticks.

Comfortably below the shortest schedule cadence (two hours), and matched by
the lookback window `/schedules/tick` itself applies — see
``services.schedule_service.TICK_LOOKBACK``. Calling it this often is safe:
every enqueue it triggers is idempotent, so an extra call, or several worker
replicas each calling it on their own timer, never double-fires anything.
"""

DEFAULT_TIMEOUT_SECONDS = 600
"""Fallback timeout when a run carries none."""


class RunnerError(RuntimeError):
    """Raised when the worker cannot continue, such as an unreachable API."""


class Worker:
    """Claims queued runs and executes their pytest targets.

    Attributes:
        api_url: NOC API base path.
        worker_id: Identifier recorded against each run it executes.
    """

    def __init__(self, api_url: str, worker_id: str | None = None) -> None:
        """Initialise the worker.

        Args:
            api_url: NOC API base path, for example ``http://localhost:8000/api``.
            worker_id: Identifier recorded against runs. Defaults to the hostname,
                which is what makes it possible to tell two workers apart in the
                run history.
        """
        self.api_url = api_url.rstrip("/")
        self.worker_id = worker_id or f"runner@{socket.gethostname()}"
        self._session = requests.Session()

    # -- API ---------------------------------------------------------------
    def fetch_queued(self, limit: int = 10) -> list[dict[str, Any]]:
        """Read the queued runs, oldest first.

        Args:
            limit: Maximum runs to return.

        Returns:
            The queued runs, empty when there is no work.

        Raises:
            RunnerError: If the API is unreachable or returns an error.
        """
        try:
            response = self._session.get(
                f"{self.api_url}/runs",
                params={"status": "queued", "sort": "started_at", "direction": "asc",
                        "limit": limit},
                timeout=10,
            )
            response.raise_for_status()
            return response.json().get("items", [])
        except requests.RequestException as error:
            raise RunnerError(f"cannot reach the API at {self.api_url}: {error}") from error

    def fetch_run(self, run_id: str) -> dict[str, Any]:
        """Read one run.

        Args:
            run_id: The run's identifier.

        Returns:
            The run.

        Raises:
            RunnerError: If it cannot be read.
        """
        try:
            response = self._session.get(f"{self.api_url}/runs/{run_id}", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as error:
            raise RunnerError(f"cannot read run {run_id}: {error}") from error

    def report_failure(self, run_id: str, reason: str, error_type: str) -> None:
        """Record a failure the suite could not report itself.

        Used when pytest crashed before reporting, or was killed on timeout. Fails
        soft, because a worker that dies while reporting a failure would leave the
        run stuck in ``running`` forever.

        Args:
            run_id: The run to fail.
            reason: Human-readable explanation.
            error_type: Category for the dashboard's error chart.
        """
        try:
            self._session.post(
                f"{self.api_url}/runs/{run_id}/complete",
                json={
                    "status": "failed",
                    "failureFeature": "הרצת האוטומציה",
                    "failureErrorType": error_type,
                    "failureReason": reason[:4000],
                },
                timeout=10,
            )
        except requests.RequestException as error:
            print(f"[worker] could not report failure for {run_id}: {error}")

    # -- execution ---------------------------------------------------------
    def execute(self, run: dict[str, Any]) -> bool:
        """Execute one run's pytest target.

        The ``runnerTarget`` recorded on the run is a pytest node id such as
        ``harmony_automations/tests/test_smoke.py::test_site_is_reachable``. It is
        passed straight to pytest, which is what ties a database row to a real
        test on disk.

        Args:
            run: The run, as returned by the API.

        Returns:
            True if pytest reported success, False otherwise.
        """
        run_id = run["id"]
        target = run.get("runnerTarget") or ""
        timeout = run.get("timeoutSeconds") or DEFAULT_TIMEOUT_SECONDS

        if not target:
            self.report_failure(run_id, "לריצה לא הוגדר יעד הרצה", "תצורה שגויה")
            return False

        print(f"[worker] running {target} (run {run_id})")

        # NOC_RUN_ID is what switches the suite's reporting on. Without it the
        # same tests run identically but report nothing.
        env = {
            **os.environ,
            "NOC_RUN_ID": run_id,
            "NOC_API_URL": self.api_url,
            "NOC_WORKER_ID": self.worker_id,
        }

        try:
            completed = subprocess.run(
                [sys.executable, "-m", "pytest", target, "-v", "--no-header"],
                cwd=str(AUTOMATIONS_ROOT),
                env=env,
                timeout=timeout,
                capture_output=True,
                text=True,
            )
        except subprocess.TimeoutExpired:
            print(f"[worker] {target} exceeded {timeout}s")
            self.report_failure(
                run_id, f"האוטומציה חרגה ממגבלת הזמן ({timeout} שניות)", "פסק זמן בתגובה"
            )
            return False
        except Exception as error:
            self.report_failure(run_id, f"הרצת האוטומציה נכשלה: {error}", "שגיאה כללית")
            return False

        if completed.returncode == 0:
            print(f"[worker] {target} passed")
            return True

        # Exit code 4 means pytest could not collect the target at all, which is a
        # configuration problem rather than a test failure — worth saying plainly
        # instead of showing an operator a collection traceback.
        if completed.returncode == 4:
            self.report_failure(
                run_id,
                f"pytest לא הצליח לאתר את היעד '{target}'. ודאו שהנתיב קיים.",
                "תצורה שגויה",
            )
            return False

        # Any other non-zero code is a real test failure, which the suite has
        # already reported in detail. Only report here if it did not, which shows
        # up as the run still being in flight.
        print(f"[worker] {target} failed (exit {completed.returncode})")
        tail = (completed.stdout or completed.stderr or "")[-1500:]

        if self._still_in_flight(run_id):
            self.report_failure(
                run_id, tail or "האוטומציה נכשלה ללא פירוט", "שגיאה כללית"
            )
        return False

    def _still_in_flight(self, run_id: str) -> bool:
        """Test whether a run never reached a terminal status.

        Args:
            run_id: The run to check.

        Returns:
            True when the run is still queued or running, meaning the suite died
            before reporting. Returns False on any error, so an API problem does
            not cause a duplicate failure report.
        """
        try:
            return self.fetch_run(run_id).get("status") in {"queued", "running"}
        except RunnerError:
            return False

    # -- scheduling ----------------------------------------------------------
    def tick_schedules(self) -> None:
        """Ask the API to enqueue any scheduled automation that has come due.

        Fails soft: an unreachable API here must not take down the run-draining
        loop, and the next tick — from this worker or another replica — will
        simply catch up, since firing is idempotent.
        """
        try:
            response = self._session.post(f"{self.api_url}/schedules/tick", timeout=10)
            response.raise_for_status()
            enqueued = response.json().get("enqueued", 0)
            if enqueued:
                print(f"[worker] schedule tick enqueued {enqueued} run(s)")
        except requests.RequestException as error:
            print(f"[worker] schedule tick failed: {error}")

    # -- loops -------------------------------------------------------------
    def run_once(self) -> int:
        """Execute every currently queued run, then return.

        Returns:
            The number of runs executed.
        """
        queued = self.fetch_queued()
        for run in queued:
            self.execute(run)
        return len(queued)

    def run_forever(self) -> None:
        """Poll for queued runs until interrupted.

        An unreachable API is retried rather than fatal: the backend restarting
        should not require restarting the worker. A scheduler tick runs on its
        own timer alongside the queue poll — this is the entire scheduling
        mechanism; there is no separate cron process.
        """
        print(f"[worker] {self.worker_id} polling {self.api_url}")

        # Ticking immediately on start means a scheduled run overdue from
        # before the worker came up fires right away rather than waiting a
        # full interval.
        last_tick = time.monotonic() - TICK_INTERVAL_SECONDS

        while True:
            try:
                if time.monotonic() - last_tick >= TICK_INTERVAL_SECONDS:
                    self.tick_schedules()
                    last_tick = time.monotonic()

                if self.run_once() == 0:
                    time.sleep(POLL_INTERVAL_SECONDS)
            except RunnerError as error:
                print(f"[worker] {error}; retrying in 5s")
                time.sleep(5)
            except KeyboardInterrupt:
                print("\n[worker] stopped")
                return


def main() -> None:
    """Parse arguments and start the worker."""
    parser = argparse.ArgumentParser(description="Execute queued NOC automation runs")
    parser.add_argument(
        "--api-url",
        default=os.environ.get("NOC_API_URL", "http://localhost:8000/api"),
        help="NOC API base path",
    )
    parser.add_argument("--worker-id", default=None, help="identifier recorded against runs")
    parser.add_argument("--once", action="store_true", help="drain the queue and exit")
    parser.add_argument("--run-id", default=None, help="execute one specific run and exit")
    args = parser.parse_args()

    worker = Worker(args.api_url, args.worker_id)

    if args.run_id:
        worker.execute(worker.fetch_run(args.run_id))
    elif args.once:
        count = worker.run_once()
        print(f"[worker] executed {count} run(s)")
    else:
        worker.run_forever()


if __name__ == "__main__":
    main()
