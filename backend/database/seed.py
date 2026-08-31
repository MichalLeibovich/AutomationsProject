"""Database seed.

Registers the applications and their automations, so the catalog exists before
anything runs. Every ``runner_target`` here is a real pytest node id in the
automation suite — that string is what the runner passes to pytest, so a typo
means the dashboard shows an automation that cannot execute.

Run history is **not** fabricated. Runs appear when automations actually execute
and report their results. ``--demo-history`` exists only for looking at the
dashboard before that has ever happened.

Usage::

    python -m database.seed
    python -m database.seed --skip-schema
    python -m database.seed --demo-history 30
"""

from __future__ import annotations

import argparse
import random
from datetime import UTC, datetime, timedelta
from typing import Any

from config.logging_config import configure_logging
from database.connection import apply_schema, init_pool, transaction
from utils.logger import get_logger

logger = get_logger(__name__)

APPLICATIONS: list[tuple[str, str, str, str, int]] = [
    ("מגן עליון", "magen-elyon", "#3B82F6", "magen_elyon_automations", 1),
    ("הרמוניה", "harmony", "#10B981", "harmony_automations", 2),
    ("גאוסיין", "gaussian", "#F59E0B", "gaussian_automations", 3),
    ("אפקט הפרפר", "butterfly-effect", "#8B5CF6", "butterfly_effect_automations", 4),
]
"""Applications as ``(name, slug, colour, automation folder, display order)``.

The fourth element is the folder the automations live in, which is what makes
each application's node ids distinct.
"""

SCHEDULES: list[tuple[str, int]] = [
    ("magen-elyon", 2),
    ("harmony", 2),
    ("gaussian", 4),
    ("butterfly-effect", 4),
]
"""Recurring schedules as ``(application slug, every_hours)``.

Magen Elyon and Harmony run their main test every two hours; Gaussian and
Butterfly Effect every four, both anchored to local midnight in
Asia/Jerusalem (the schedule's default timezone and anchor minute).
"""

MAIN_TEST: tuple[str, str] = (
    "בדיקת שפיות - טעינת האתר",
    "tests/test_smoke.py::test_site_is_reachable",
)
"""The main automation, as ``(display name, node id within the app folder)``."""

SECONDARY_TESTS: list[tuple[str, str]] = [
    ("בדיקת חיפוש", "tests/test_smoke.py::test_search_returns_results"),
    ("בדיקת הצגת לוגו", "tests/test_checks.py::test_logo_is_displayed"),
    ("בדיקת כתובת הדף", "tests/test_checks.py::test_page_url_is_correct"),
]
"""Secondary automations, created for every application."""

GENERAL_TESTS: list[tuple[str, str]] = [
    (
        "בדיקת קישוריות חיצונית",
        "general_automations/tests/test_environment.py::test_external_connectivity",
    ),
    (
        "בדיקת זמן טעינה",
        "general_automations/tests/test_environment.py::test_page_load_within_budget",
    ),
    (
        "בדיקת טיפול בהודעת הסכמה",
        "general_automations/tests/test_environment.py::test_consent_banner_is_handled",
    ),
]
"""General automations. Full node ids, since they belong to no application."""

FAILURE_FEATURES = ["פתיחת אתר היעד", "אימות טעינת הדף", "ביצוע חיפוש", "אימות תוצאות"]
"""Step names drawn from when generating demo history."""

ERROR_TYPES = ["פסק זמן בתגובה", "אלמנט לא נמצא", "שגיאת רשת", "אימות נכשל"]
"""Failure categories drawn from when generating demo history."""


def seed_applications(cursor: Any) -> list[dict[str, Any]]:
    """Insert or update the applications.

    Args:
        cursor: Cursor inside an open transaction.

    Returns:
        One mapping per application, with ``id``, ``name``, ``slug`` and the
        automation ``folder``.
    """
    rows: list[dict[str, Any]] = []

    for name, slug, color, folder, order in APPLICATIONS:
        cursor.execute(
            """
            INSERT INTO noc.applications (name, slug, color, display_order)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (slug) DO UPDATE
              SET name = EXCLUDED.name, color = EXCLUDED.color,
                  display_order = EXCLUDED.display_order, is_active = true
            RETURNING id, name, slug
            """,
            (name, slug, color, order),
        )
        row = dict(cursor.fetchone())
        row["folder"] = folder
        rows.append(row)

    logger.info("applications seeded", extra={"count": len(rows)})
    return rows


def _register(
    cursor: Any,
    *,
    application_id: str | None,
    scope: str,
    kind: str,
    name: str,
    runner_target: str,
    display_order: int,
) -> None:
    """Register one automation in the catalog.

    Upserts on ``runner_target``, so re-seeding never accumulates duplicates.

    Args:
        cursor: Cursor inside an open transaction.
        application_id: Owning application, or None for general automation.
        scope: ``application`` or ``general``.
        kind: ``main``, ``secondary`` or ``general``.
        name: Display name shown on the dashboard.
        runner_target: The pytest node id the runner executes.
        display_order: Sort position within its card.
    """
    cursor.execute(
        """
        INSERT INTO noc.test_definitions
            (application_id, scope, kind, name, runner_target, display_order)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (runner_target) DO UPDATE
          SET name = EXCLUDED.name,
              display_order = EXCLUDED.display_order,
              is_active = true,
              archived_at = NULL
        """,
        (application_id, scope, kind, name, runner_target, display_order),
    )


def archive_stale_automations(cursor: Any, live_targets: list[str]) -> int:
    """Retire catalog rows whose automation is no longer defined here.

    Without this the seed only ever adds. Re-seeding after renaming or removing an
    automation leaves the old row active, so the dashboard keeps offering a button
    that points at a test file which no longer exists — and pressing it produces a
    configuration error rather than a run.

    Archiving rather than deleting, because run history references these rows.

    Args:
        cursor: Cursor inside an open transaction.
        live_targets: Every ``runner_target`` this seed just registered.

    Returns:
        The number of automations archived.
    """
    cursor.execute(
        """
        UPDATE noc.test_definitions
           SET is_active = false, archived_at = now()
         WHERE is_active
           AND runner_target <> ALL(%s)
        RETURNING runner_target
        """,
        (live_targets,),
    )
    stale = [row["runner_target"] for row in cursor.fetchall()]

    if stale:
        logger.info("archived stale automations", extra={"count": len(stale), "targets": stale})
    return len(stale)


def build_catalog(applications: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Resolve the full catalog before anything is written.

    Building the list up front is what lets stale rows be archived *before* the
    new ones are inserted. The database permits only one active main test per
    application, so inserting a renamed main while the old one is still active
    violates that index.

    Args:
        applications: Applications returned by :func:`seed_applications`.

    Returns:
        One mapping per automation, ready to pass to :func:`_register`.
    """
    catalog: list[dict[str, Any]] = []

    for application in applications:
        folder = application["folder"]

        name, target = MAIN_TEST
        catalog.append(
            {
                "application_id": application["id"],
                "scope": "application",
                "kind": "main",
                "name": name,
                "runner_target": f"{folder}/{target}",
                "display_order": 0,
            }
        )

        for order, (secondary_name, secondary_target) in enumerate(SECONDARY_TESTS, start=1):
            catalog.append(
                {
                    "application_id": application["id"],
                    "scope": "application",
                    "kind": "secondary",
                    "name": secondary_name,
                    "runner_target": f"{folder}/{secondary_target}",
                    "display_order": order,
                }
            )

    for order, (name, target) in enumerate(GENERAL_TESTS, start=1):
        catalog.append(
            {
                "application_id": None,
                "scope": "general",
                "kind": "general",
                "name": name,
                "runner_target": target,
                "display_order": order,
            }
        )

    return catalog


def archive_stale_automations(cursor: Any, live_targets: list[str]) -> int:
    """Retire catalog rows whose automation is no longer defined here.

    Must run *before* the new rows are inserted. An automation that was renamed
    keeps its old row otherwise, and since only one main test per application may
    be active, inserting the replacement would fail on a unique violation.

    Archiving rather than deleting, because run history references these rows.

    Args:
        cursor: Cursor inside an open transaction.
        live_targets: Every ``runner_target`` about to be registered.

    Returns:
        The number of automations archived.
    """
    cursor.execute(
        """
        UPDATE noc.test_definitions
           SET is_active = false, archived_at = now()
         WHERE is_active
           AND runner_target <> ALL(%s)
        RETURNING runner_target
        """,
        (live_targets,),
    )
    stale = [row["runner_target"] for row in cursor.fetchall()]

    if stale:
        logger.info("archived stale automations", extra={"count": len(stale), "targets": stale})
    return len(stale)


def seed_automations(cursor: Any, applications: list[dict[str, Any]]) -> int:
    """Register every automation in the catalog.

    Application node ids are prefixed with the application's own folder, so the
    same test name in two applications produces two distinct catalog rows — which
    the unique constraint on ``runner_target`` requires.

    Order matters: stale rows are archived first, then the current catalog is
    written. Doing it the other way round trips the one-main-per-application
    index whenever a main test has been renamed.

    Args:
        cursor: Cursor inside an open transaction.
        applications: Applications returned by :func:`seed_applications`.

    Returns:
        The number of automations registered.
    """
    catalog = build_catalog(applications)

    archived = archive_stale_automations(cursor, [entry["runner_target"] for entry in catalog])

    for entry in catalog:
        _register(cursor, **entry)

    logger.info(
        "automations registered", extra={"count": len(catalog), "archived": archived}
    )
    return len(catalog)


def seed_schedules(cursor: Any, applications: list[dict[str, Any]]) -> int:
    """Register the recurring schedule of every application that has one.

    Upserts on ``application_id`` (the table's unique key), so re-seeding
    never accumulates duplicate schedules.

    Args:
        cursor: Cursor inside an open transaction.
        applications: Applications returned by :func:`seed_applications`,
            used to resolve each slug to an id.

    Returns:
        The number of schedules registered.
    """
    by_slug = {application["slug"]: application["id"] for application in applications}
    registered = 0

    for slug, every_hours in SCHEDULES:
        application_id = by_slug.get(slug)
        if application_id is None:
            logger.warning("schedule references unknown application", extra={"slug": slug})
            continue

        cursor.execute(
            """
            INSERT INTO noc.schedules (application_id, every_hours)
            VALUES (%s, %s)
            ON CONFLICT (application_id) DO UPDATE
              SET every_hours = EXCLUDED.every_hours, is_active = true
            """,
            (application_id, every_hours),
        )
        registered += 1

    logger.info("schedules seeded", extra={"count": registered})
    return registered


def ensure_partitions(cursor: Any, days: int) -> None:
    """Create every run partition the generated range will need.

    The month count is derived from ``days`` rather than hardcoded: seeding
    seventy-five days into three months of partitions fails at insert time.

    Args:
        cursor: Cursor inside an open transaction.
        days: Days of history about to be generated.
    """
    months = days // 28 + 2

    for offset in range(-months, 3):
        cursor.execute(
            """
            SELECT noc.ensure_run_partition(
                (date_trunc('month', CURRENT_DATE) + (%s || ' months')::interval)::date
            )
            """,
            (offset,),
        )


def seed_demo_history(cursor: Any, days: int) -> int:
    """Generate demo run history, unless runs already exist.

    Only for looking at the dashboard before the automations have ever run. Every
    generated row is tagged ``demo-seed`` so it is distinguishable from a real
    result.

    Args:
        cursor: Cursor inside an open transaction.
        days: Days of history to generate, counting back from today.

    Returns:
        The number of runs inserted, or 0 if the table was already populated.
    """
    cursor.execute("SELECT count(*) AS total FROM noc.test_runs")
    if int(cursor.fetchone()["total"]) > 0:
        logger.info("runs already exist, skipping demo history")
        return 0

    ensure_partitions(cursor, days)

    cursor.execute(
        """
        SELECT d.id, d.name, d.runner_target, d.scope, d.application_id,
               COALESCE(a.name, 'כללי') AS scope_label
        FROM noc.test_definitions d
        LEFT JOIN noc.applications a ON a.id = d.application_id
        WHERE d.is_active
        """
    )
    definitions = [dict(row) for row in cursor.fetchall()]
    inserted = 0
    now = datetime.now(UTC)

    for day_offset in range(days):
        day = now - timedelta(days=day_offset)
        # Friday and Saturday are quieter in an Israeli operations rota.
        runs_today = random.randint(2, 5) if day.weekday() in (4, 5) else random.randint(6, 14)

        for _ in range(runs_today):
            definition = random.choice(definitions)
            started = day.replace(
                hour=random.randint(6, 22), minute=random.randint(0, 59), second=0, microsecond=0
            )
            duration = random.randint(8, 90)
            failed = random.random() < 0.17
            steps = random.randint(3, 5)

            cursor.execute(
                """
                INSERT INTO noc.test_runs
                    (test_definition_id, application_id, scope, scope_label, test_name,
                     runner_target, status, queued_at, started_at, ended_at,
                     triggered_by, trigger_source, total_steps, failed_steps,
                     failure_feature, failure_error_type, failure_reason)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'schedule', %s, %s, %s, %s, %s)
                """,
                (
                    definition["id"],
                    definition["application_id"],
                    definition["scope"],
                    definition["scope_label"],
                    definition["name"],
                    definition["runner_target"],
                    "failed" if failed else "passed",
                    started,
                    started,
                    started + timedelta(seconds=duration),
                    "demo-seed",
                    steps,
                    1 if failed else 0,
                    random.choice(FAILURE_FEATURES) if failed else None,
                    random.choice(ERROR_TYPES) if failed else None,
                    "ריצת הדגמה שנכשלה לצורך תצוגת נתונים." if failed else None,
                ),
            )
            inserted += 1

    logger.info("demo history generated", extra={"count": inserted, "days": days})
    return inserted


def main() -> None:
    """Apply the schema if requested, then seed the catalog.

    Raises:
        RuntimeError: If ``DATABASE_URL`` is unset.
        psycopg2.Error: If the schema cannot be applied or a seed insert fails.
    """
    parser = argparse.ArgumentParser(description="Seed the NOC automation database")
    parser.add_argument("--skip-schema", action="store_true", help="assume the schema exists")
    parser.add_argument(
        "--demo-history",
        type=int,
        default=0,
        metavar="DAYS",
        help="generate this many days of fake run history for a first look",
    )
    args = parser.parse_args()

    configure_logging()
    init_pool()

    if not args.skip_schema:
        apply_schema()

    with transaction() as cursor:
        applications = seed_applications(cursor)
        automations = seed_automations(cursor, applications)
        schedules = seed_schedules(cursor, applications)
        history = seed_demo_history(cursor, args.demo_history) if args.demo_history else 0

    if history:
        with transaction() as cursor:
            cursor.execute("SELECT noc.refresh_daily_run_stats()")

    print(
        f"Seed complete: {len(applications)} applications, "
        f"{automations} automations, {schedules} schedules, {history} demo runs"
    )


if __name__ == "__main__":
    main()
