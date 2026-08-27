"""Run step persistence.

Steps are what turn a bare pass or fail into something diagnosable: which part of
the automation broke, how long each part took, and what the error was.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Sequence
from uuid import UUID

from database import queries
from database.connection import transaction
from database.models import RunStep
from repositories.base_repository import BaseRepository
from utils.logger import get_logger

logger = get_logger(__name__)


class StepRepository(BaseRepository):
    """Reads and writes the per-step detail of a run."""

    def list_by_run(self, run_id: UUID) -> list[RunStep]:
        """List a run's steps in execution order.

        Args:
            run_id: The run whose steps to read.

        Returns:
            Steps ordered by index.
        """
        rows = self.fetch_all(queries.SELECT_STEPS_BY_RUN, {"run_id": str(run_id)})
        return self.map_all(rows, RunStep.from_row)

    def record_batch(
        self, *, run_id: UUID, run_started_at: datetime, steps: Sequence[dict[str, Any]]
    ) -> list[RunStep]:
        """Store a batch of steps and refresh the run's tallies.

        Written as one batch rather than one request per step, so a twenty-step
        automation costs one round trip. Each step upserts on its index, so a
        retried batch replaces rather than failing on the unique constraint.

        The run's ``total_steps`` and ``failed_steps`` are recomputed from the
        stored rows rather than incremented, so a retry cannot double-count.

        Args:
            run_id: The run these steps belong to.
            run_started_at: The run's start time, needed for the composite
                foreign key into the partitioned runs table.
            steps: Cleaned step mappings, each with ``step_index``, ``name``,
                ``status``, ``duration_ms`` and ``error_message``.

        Returns:
            The stored steps.

        Raises:
            psycopg2.Error: If the transaction fails, for example because the
                composite foreign key does not resolve.
        """
        stored: list[dict[str, Any]] = []

        with transaction() as cursor:
            for step in steps:
                cursor.execute(
                    queries.INSERT_STEP,
                    {
                        "run_id": str(run_id),
                        "run_started_at": run_started_at,
                        "step_index": step["step_index"],
                        "name": step["name"],
                        "status": step["status"],
                        "duration_ms": step["duration_ms"],
                        "error_message": step.get("error_message"),
                    },
                )
                row = cursor.fetchone()
                if row is not None:
                    stored.append(dict(row))

            cursor.execute(queries.UPDATE_RUN_STEP_COUNTS, {"run_id": str(run_id)})

        logger.info("steps recorded", extra={"run_id": str(run_id), "count": len(stored)})
        return self.map_all(stored, RunStep.from_row)
