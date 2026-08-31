"""SQL text, as named constants and small composition helpers.

Every statement in the system lives here, which makes the whole query surface
greppable in one file. Repositories execute these constants; nothing in this
module opens a connection.

Three rules hold throughout:

* Every value is a bound parameter. No f-string ever carries request data.
* Parameters used only in ``IS NULL`` comparisons carry an explicit cast, because
  PostgreSQL cannot infer a type from ``IS NULL`` alone and rejects the statement
  with "could not determine data type of parameter".
* Dynamic ``ORDER BY`` clauses and column names resolve through the whitelists in
  :mod:`utils.constants` and are interpolated as identifiers, never as
  caller-supplied text.
"""

from __future__ import annotations

from utils.constants import SORT_DIRECTIONS, SORTABLE_RUN_COLUMNS

# ===========================================================================
# Applications
# ===========================================================================
SELECT_APPLICATIONS = """
    SELECT id, name, slug, color, display_order, is_active
    FROM noc.applications
    WHERE (%(include_inactive)s OR is_active)
    ORDER BY display_order, name
"""
"""List applications, optionally including deactivated ones."""

SELECT_APPLICATION_BY_ID = """
    SELECT id, name, slug, color, display_order, is_active
    FROM noc.applications
    WHERE id = %(application_id)s
"""
"""Load one application by primary key."""

UPSERT_APPLICATION = """
    INSERT INTO noc.applications (name, slug, color, display_order)
    VALUES (%(name)s, %(slug)s, %(color)s, %(display_order)s)
    ON CONFLICT (slug) DO UPDATE
      SET name = EXCLUDED.name,
          color = EXCLUDED.color,
          display_order = EXCLUDED.display_order,
          is_active = true
    RETURNING id, name, slug, color, display_order, is_active
"""
"""Create or update an application, keyed on its slug."""

UPDATE_APPLICATION = """
    UPDATE noc.applications
       SET name          = COALESCE(%(name)s, name),
           color         = COALESCE(%(color)s, color),
           display_order = COALESCE(%(display_order)s, display_order),
           is_active     = COALESCE(%(is_active)s, is_active)
     WHERE id = %(application_id)s
    RETURNING id, name, slug, color, display_order, is_active
"""
"""Update an application's mutable fields, ignoring null arguments."""

DEACTIVATE_APPLICATION = """
    UPDATE noc.applications SET is_active = false
     WHERE id = %(application_id)s AND is_active
"""
"""Hide an application without deleting it, since run history references it."""

# ===========================================================================
# Test definitions
# ===========================================================================
DEFINITION_PROJECTION = """
    SELECT d.id, d.application_id, d.scope, d.kind, d.name, d.description,
           d.runner_target, d.display_order, d.timeout_seconds, d.is_active,
           a.name AS application_name
    FROM noc.test_definitions d
    LEFT JOIN noc.applications a ON a.id = d.application_id
"""
"""Shared column list for definition queries, so the projection cannot drift."""

SELECT_TEST_DEFINITIONS = (
    DEFINITION_PROJECTION
    + """
    WHERE d.is_active
      AND (
        (%(scope)s::text IS NULL     AND d.scope = 'application') OR
        (%(scope)s::text = 'general' AND d.scope = 'general')     OR
        (%(scope)s::text IS NOT NULL AND %(scope)s::text <> 'general' AND a.name = %(scope)s::text)
      )
    ORDER BY (d.kind <> 'main'), a.display_order NULLS FIRST, d.display_order, d.name
"""
)
"""List active definitions for a scope.

``scope`` mirrors the interface: null selects application-scoped definitions,
``'general'`` selects general automation, and any other value selects that
application by name. Main tests sort ahead of secondary ones.
"""

SELECT_TEST_DEFINITION_BY_ID = DEFINITION_PROJECTION + " WHERE d.id = %(definition_id)s"
"""Load one definition by primary key, with its application name joined."""

SELECT_DEFINITION_BY_TARGET = (
    DEFINITION_PROJECTION + " WHERE d.runner_target = %(runner_target)s AND d.is_active"
)
"""Load a definition by its pytest node id.

This is how a runner resolves the automation it just executed back to a catalog
row without needing to know any database identifier.
"""

SELECT_MAIN_DEFINITION_FOR_APPLICATION = (
    DEFINITION_PROJECTION
    + """
    WHERE d.is_active
      AND d.kind = 'main'
      AND d.scope = 'application'
      AND d.application_id = %(application_id)s
"""
)
"""Load the current active main test of one application, by id.

Used by the scheduler at tick time, so a schedule always fires whatever
automation is *currently* the application's main test, surviving that test
being renamed (which archives the old definition and creates a new one).
"""

SELECT_MAIN_DEFINITIONS_FOR_BULK = (
    DEFINITION_PROJECTION
    + """
    WHERE d.is_active
      AND d.kind = 'main'
      AND d.scope = 'application'
      AND a.is_active
      AND (%(scope)s::text IS NULL OR a.name = %(scope)s::text)
    ORDER BY a.display_order, a.name
"""
)
"""List the main test of every active application in scope.

General automation is excluded by the query itself rather than by a caller, so no
code path can bulk-trigger it.
"""

INSERT_TEST_DEFINITION = """
    INSERT INTO noc.test_definitions
        (application_id, scope, kind, name, description, runner_target,
         display_order, timeout_seconds)
    VALUES
        (%(application_id)s, %(scope)s, %(kind)s, %(name)s, %(description)s,
         %(runner_target)s, %(display_order)s, %(timeout_seconds)s)
    ON CONFLICT (runner_target) DO UPDATE
      SET name            = EXCLUDED.name,
          description     = EXCLUDED.description,
          display_order   = EXCLUDED.display_order,
          timeout_seconds = EXCLUDED.timeout_seconds,
          is_active       = true,
          archived_at     = NULL
    RETURNING id, application_id, scope, kind, name, description, runner_target,
              display_order, timeout_seconds, is_active
"""
"""Create a definition, or update the existing one with the same node id.

Upsert rather than plain insert, so re-registering the catalog from the
automation suite is idempotent.
"""

ARCHIVE_TEST_DEFINITION = """
    UPDATE noc.test_definitions
       SET is_active = false, archived_at = now()
     WHERE id = %(definition_id)s AND is_active
"""
"""Archive a definition. A soft delete, so run history survives."""

# ===========================================================================
# Runs
# ===========================================================================
RUN_PROJECTION = """
    SELECT r.id, r.test_definition_id, r.test_name, r.runner_target,
           r.application_id, r.scope, r.scope_label, r.status,
           r.queued_at, r.started_at, r.ended_at, r.duration_seconds,
           r.triggered_by, r.trigger_source, r.worker_id, r.attempt,
           r.total_steps, r.failed_steps, r.artifact_count,
           r.failure_feature, r.failure_error_type, r.failure_reason, r.stack_trace,
           r.idempotency_key
    FROM noc.test_runs r
"""
"""Shared column list for every run query, so the projection cannot drift."""

RUN_FILTER = """
    WHERE (%(scope)s::text IS NULL OR
           (%(scope)s::text = 'general' AND r.scope = 'general') OR
           (%(scope)s::text <> 'general' AND r.scope_label = %(scope)s::text))
      AND (%(status)s::text IS NULL OR r.status = %(status)s::noc.run_status)
      AND (%(trigger_source)s::text IS NULL OR
           r.trigger_source = %(trigger_source)s::noc.trigger_source)
      AND (%(search)s::text IS NULL OR
           r.search_text LIKE '%%' || lower(%(search)s::text) || '%%')
      AND (%(date_from)s::timestamptz IS NULL OR r.started_at >= %(date_from)s::timestamptz)
      AND (%(date_to)s::timestamptz   IS NULL OR r.started_at <= %(date_to)s::timestamptz)
"""
"""Shared WHERE clause for run queries.

Search is a substring match, not a full-text one: an operator hunting for a run
types a fragment of what they remember, so "רמו" has to find "הרמוני". Full-text
search matches whole words and would return nothing for that. The column is
lowercased by the database and the term is lowercased here, which makes the match
case-insensitive without a function call that would defeat the index.

``%%`` rather than ``%`` because psycopg2 treats a lone ``%`` as the start of a
placeholder.

Every parameter carries an explicit cast; PostgreSQL cannot infer a type from an
``IS NULL`` comparison alone.
"""

COUNT_RUNS = "SELECT count(*) AS total FROM noc.test_runs r " + RUN_FILTER
"""Count runs matching the shared filter, for pagination totals."""

SELECT_RUN_BY_ID = RUN_PROJECTION + " WHERE r.id = %(run_id)s"
"""Load one run by primary key."""

SELECT_ACTIVE_RUNS = """
    SELECT * FROM (
      SELECT DISTINCT ON (r.test_definition_id)
             r.id, r.test_definition_id, r.status, r.started_at, r.ended_at,
             r.duration_seconds, r.failure_reason, r.trigger_source, r.scope_label,
             r.test_name
      FROM noc.test_runs r
      WHERE r.status IN ('queued', 'running')
         OR r.ended_at > now() - %(settle_window)s::interval
      ORDER BY r.test_definition_id, r.started_at DESC
    ) latest
    ORDER BY latest.started_at DESC
    LIMIT %(limit)s
"""
"""List the latest run of each automation for the live stream.

``DISTINCT ON`` is what makes this correct rather than merely tidy. The interface
tracks one status per automation, so emitting two runs of the same automation
means the second frame overwrites the first. Re-running an automation within the
settle window would otherwise send both the new queued run and the previous
finished one, and the older frame would land last — the row would flash "בריצה"
and then drop back to "עברה" while the new run was still starting.

Covers everything in flight, plus anything that just finished.

The second clause is essential rather than a nicety. A run that reaches a
terminal status stops matching the first clause, so it would simply vanish from
the feed — and a client that never receives a terminal frame keeps showing its
last known state, which is "running", with the elapsed clock ticking forever.

Including recently-ended runs for a short window guarantees every client sees the
transition, even one that reconnected moments earlier.
"""

ENSURE_PARTITION_FOR_TODAY = "SELECT noc.ensure_run_partition(CURRENT_DATE)"
"""Create today's run partition if it does not yet exist."""

ENSURE_PARTITION_AT_OFFSET = """
    SELECT noc.ensure_run_partition(
        (date_trunc('month', CURRENT_DATE) + (%(offset_months)s || ' months')::interval)::date
    ) AS partition_name
"""
"""Create the run partition a given number of months from today."""

DROP_PARTITIONS_BEFORE = "SELECT noc.drop_run_partitions_before(%(cutoff)s) AS dropped"
"""Drop run partitions entirely below a cutoff date.

Retention is a metadata operation rather than a mass row delete, which keeps it
fast as history grows.
"""

PRUNE_IDEMPOTENCY_CLAIMS = "SELECT noc.prune_idempotency_claims() AS removed"
"""Delete idempotency claims older than the retention interval."""

CLAIM_IDEMPOTENCY_KEY = """
    INSERT INTO noc.run_idempotency (idempotency_key, run_id, run_started_at)
    VALUES (%(idempotency_key)s, %(run_id)s, %(run_started_at)s)
    ON CONFLICT (idempotency_key) DO NOTHING
    RETURNING run_id
"""
"""Claim an idempotency key, returning nothing if it is already claimed."""

SELECT_RUN_BY_IDEMPOTENCY_KEY = (
    RUN_PROJECTION
    + """
    JOIN noc.run_idempotency k
      ON k.run_id = r.id AND k.run_started_at = r.started_at
    WHERE k.idempotency_key = %(idempotency_key)s
"""
)
"""Load the run previously created for an idempotency key."""

INSERT_RUN = """
    INSERT INTO noc.test_runs
        (id, test_definition_id, application_id, scope, scope_label, test_name,
         runner_target, status, started_at, triggered_by, trigger_source,
         idempotency_key, correlation_id)
    VALUES
        (%(run_id)s, %(definition_id)s, %(application_id)s, %(scope)s,
         %(scope_label)s, %(test_name)s, %(runner_target)s, 'queued',
         %(started_at)s, %(triggered_by)s, %(trigger_source)s,
         %(idempotency_key)s, %(correlation_id)s)
    RETURNING id, test_definition_id, test_name, runner_target, application_id,
              scope, scope_label, status, queued_at, started_at, ended_at,
              duration_seconds, triggered_by, trigger_source, worker_id, attempt,
              total_steps, failed_steps, artifact_count,
              failure_feature, failure_error_type, failure_reason, stack_trace,
              idempotency_key
"""
"""Insert a queued run with its scope label frozen at insert time."""

MARK_RUN_RUNNING = """
    WITH claimed AS (
        UPDATE noc.test_runs
           SET status = 'running', worker_id = %(worker_id)s, started_at = now()
         WHERE id = %(run_id)s AND status = 'queued'
        RETURNING id, test_definition_id, test_name, runner_target, application_id,
                  scope, scope_label, status, queued_at, started_at, ended_at,
                  duration_seconds, triggered_by, trigger_source, worker_id, attempt,
                  total_steps, failed_steps, artifact_count,
                  failure_feature, failure_error_type, failure_reason, stack_trace,
                  idempotency_key
    ), synced AS (
        UPDATE noc.run_idempotency
           SET run_started_at = claimed.started_at
          FROM claimed
         WHERE run_idempotency.run_id = claimed.id
        RETURNING 1
    )
    SELECT claimed.* FROM claimed LEFT JOIN synced ON true
"""
"""Transition a queued run to running.

The status guard makes the claim atomic, so two workers cannot both win.

Also re-points the run's idempotency claim at the new ``started_at``: that
value moves forward here (to when execution actually began, not when the run
was queued), and ``run_idempotency.run_started_at`` must track it exactly,
since ``SELECT_RUN_BY_IDEMPOTENCY_KEY`` joins on both ``run_id`` and
``run_started_at`` together. Left unsynced, that join silently stops
matching the instant a run is claimed — the scheduler then sees the
occurrence as never having fired and enqueues a fresh duplicate on every
subsequent tick for as long as it stays within the lookback window. The
``LEFT JOIN ... ON true`` only exists to force the ``synced`` CTE to execute:
an unreferenced data-modifying CTE is not guaranteed to run in Postgres.
"""

COMPLETE_RUN = """
    UPDATE noc.test_runs
       SET status             = %(status)s::noc.run_status,
           ended_at           = now(),
           failure_feature    = %(failure_feature)s,
           failure_error_type = %(failure_error_type)s,
           failure_reason     = %(failure_reason)s,
           stack_trace        = %(stack_trace)s
     WHERE id = %(run_id)s AND status IN ('queued', 'running')
    RETURNING id, test_definition_id, test_name, runner_target, application_id,
              scope, scope_label, status, queued_at, started_at, ended_at,
              duration_seconds, triggered_by, trigger_source, worker_id, attempt,
              total_steps, failed_steps, artifact_count,
              failure_feature, failure_error_type, failure_reason, stack_trace,
              idempotency_key
"""
"""Transition an in-flight run to a terminal status with failure detail."""

CANCEL_RUN = """
    UPDATE noc.test_runs
       SET status = 'cancelled', ended_at = now(), failure_reason = %(reason)s
     WHERE id = %(run_id)s AND status IN ('queued', 'running')
    RETURNING id, test_definition_id, test_name, runner_target, application_id,
              scope, scope_label, status, queued_at, started_at, ended_at,
              duration_seconds, triggered_by, trigger_source, worker_id, attempt,
              total_steps, failed_steps, artifact_count,
              failure_feature, failure_error_type, failure_reason, stack_trace,
              idempotency_key
"""
"""Cancel an in-flight run.

Recorded as cancelled with a stated reason, never as a pass.
"""

# ===========================================================================
# Steps
# ===========================================================================
INSERT_STEP = """
    INSERT INTO noc.run_steps
        (run_id, run_started_at, step_index, name, status, duration_ms, error_message)
    VALUES
        (%(run_id)s, %(run_started_at)s, %(step_index)s, %(name)s,
         %(status)s::noc.step_status, %(duration_ms)s, %(error_message)s)
    ON CONFLICT (run_id, step_index) DO UPDATE
      SET name          = EXCLUDED.name,
          status        = EXCLUDED.status,
          duration_ms   = EXCLUDED.duration_ms,
          error_message = EXCLUDED.error_message
    RETURNING id, run_id, step_index, name, status, duration_ms, error_message, started_at
"""
"""Record one step, replacing an earlier report for the same index.

Upsert rather than insert, so a retried batch cannot violate the unique
constraint and lose the whole submission.
"""

SELECT_STEPS_BY_RUN = """
    SELECT id, run_id, step_index, name, status, duration_ms, error_message, started_at
    FROM noc.run_steps
    WHERE run_id = %(run_id)s
    ORDER BY step_index
"""
"""List a run's steps in execution order."""

UPDATE_RUN_STEP_COUNTS = """
    UPDATE noc.test_runs r
       SET total_steps  = s.total,
           failed_steps = s.failed
      FROM (
        SELECT count(*) AS total,
               count(*) FILTER (WHERE status = 'failed') AS failed
        FROM noc.run_steps WHERE run_id = %(run_id)s
      ) s
     WHERE r.id = %(run_id)s
"""
"""Recompute a run's step tallies from the steps actually stored.

Derived rather than incremented, so a retried batch cannot double-count.
"""

# ===========================================================================
# Artifacts
# ===========================================================================
INSERT_ARTIFACT = """
    INSERT INTO noc.run_artifacts
        (run_id, run_started_at, kind, file_name, local_path,
         s3_bucket, s3_key, content_type, size_bytes)
    VALUES
        (%(run_id)s, %(run_started_at)s, %(kind)s::noc.artifact_kind, %(file_name)s,
         %(local_path)s, %(s3_bucket)s, %(s3_key)s, %(content_type)s, %(size_bytes)s)
    RETURNING id, run_id, kind, file_name, local_path, s3_bucket, s3_key,
              content_type, size_bytes
"""
"""Record artifact metadata. The bytes themselves live outside the database."""

SELECT_ARTIFACTS_BY_RUN = """
    SELECT id, run_id, kind, file_name, local_path, s3_bucket, s3_key,
           content_type, size_bytes
    FROM noc.run_artifacts
    WHERE run_id = %(run_id)s
    ORDER BY kind, file_name
"""
"""List every artifact belonging to a run."""

UPDATE_RUN_ARTIFACT_COUNT = """
    UPDATE noc.test_runs r
       SET artifact_count = (
             SELECT count(*) FROM noc.run_artifacts WHERE run_id = %(run_id)s
           )
     WHERE r.id = %(run_id)s
"""
"""Recompute a run's artifact tally from the artifacts actually stored."""

# ===========================================================================
# Comments
# ===========================================================================
SELECT_COMMENTS_BY_RUN = """
    SELECT id, run_id, author_name, body, created_at
    FROM noc.run_comments
    WHERE run_id = %(run_id)s AND deleted_at IS NULL
    ORDER BY created_at
"""
"""List a run's comments in chronological order."""

INSERT_COMMENT = """
    INSERT INTO noc.run_comments (run_id, run_started_at, author_name, body)
    VALUES (%(run_id)s, %(run_started_at)s, %(author_name)s, %(body)s)
    RETURNING id, run_id, author_name, body, created_at
"""
"""Add a comment to a run.

The run's ``started_at`` is required because the table carries the partition key
as half of a composite foreign key.
"""

SOFT_DELETE_COMMENT = """
    UPDATE noc.run_comments
       SET deleted_at = now()
     WHERE id = %(comment_id)s AND deleted_at IS NULL
"""
"""Mark a comment deleted, retaining the row."""

# ===========================================================================
# Analytics
# ===========================================================================
DASHBOARD_STATS = """
    SELECT count(*)                                  AS total_runs,
           count(*) FILTER (WHERE r.status = 'failed') AS failed_runs,
           COALESCE(avg(r.duration_seconds) FILTER (WHERE r.duration_seconds IS NOT NULL), 0)
             AS avg_duration_seconds
    FROM noc.test_runs r
""" + RUN_FILTER
"""Aggregate headline dashboard metrics over the shared run filter."""

CALENDAR_MONTH = """
    WITH days AS (
      SELECT date_trunc('day', started_at)::date AS day,
             count(*)                                  AS total,
             count(*) FILTER (WHERE status = 'passed') AS passed,
             count(*) FILTER (WHERE status = 'failed') AS failed
      FROM noc.test_runs
      WHERE started_at >= make_date(%(year)s, %(month)s, 1)
        AND started_at <  (make_date(%(year)s, %(month)s, 1) + interval '1 month')
      GROUP BY 1
    ),
    preview AS (
      SELECT day, jsonb_agg(item ORDER BY started_at DESC) AS preview
      FROM (
        SELECT date_trunc('day', started_at)::date AS day,
               started_at,
               jsonb_build_object(
                 'id', id::text, 'scopeLabel', scope_label, 'status', status::text
               ) AS item,
               row_number() OVER (
                 PARTITION BY date_trunc('day', started_at)::date
                 ORDER BY started_at DESC
               ) AS rn
        FROM noc.test_runs
        WHERE started_at >= make_date(%(year)s, %(month)s, 1)
          AND started_at <  (make_date(%(year)s, %(month)s, 1) + interval '1 month')
      ) ranked
      WHERE rn <= %(preview_limit)s
      GROUP BY day
    )
    SELECT d.day, d.total, d.passed, d.failed, COALESCE(p.preview, '[]'::jsonb) AS preview
    FROM days d LEFT JOIN preview p ON p.day = d.day
    ORDER BY d.day
"""
"""Aggregate a month of run activity in one round trip.

Day totals and a bounded per-day preview are computed together rather than
issuing a query per day.
"""

REFRESH_DAILY_RUN_STATS = "SELECT noc.refresh_daily_run_stats() AS mode"
"""Refresh the daily rollup.

The database function chooses between a concurrent and a blocking refresh, since
the preconditions can only be checked reliably in the same transaction as the
refresh itself.
"""


# ===========================================================================
# Schedules
# ===========================================================================
SCHEDULE_PROJECTION = """
    SELECT s.id, s.application_id, s.every_hours, s.anchor_minute, s.timezone,
           s.is_active, a.name AS application_name
    FROM noc.schedules s
    JOIN noc.applications a ON a.id = s.application_id
"""
"""Shared column list for schedule queries."""

SELECT_ACTIVE_SCHEDULES = SCHEDULE_PROJECTION + " WHERE s.is_active ORDER BY a.display_order, a.name"
"""List every active recurring schedule, application name joined for display."""

SELECT_SCHEDULE_BY_ID = SCHEDULE_PROJECTION + " WHERE s.id = %(schedule_id)s"
"""Load one schedule by primary key."""

SELECT_SKIPS_IN_RANGE = """
    SELECT id, schedule_id, occurrence, created_at, restored_at
    FROM noc.schedule_skips
    WHERE schedule_id = ANY(%(schedule_ids)s::uuid[])
      AND occurrence >= %(start)s AND occurrence < %(end)s
"""
"""List every skip — active or already restored — touching a set of
schedules within a range, so the caller can distinguish a cancelled
occurrence from a restored one rather than just seeing it vanish."""

UPSERT_SCHEDULE_SKIP = """
    INSERT INTO noc.schedule_skips (schedule_id, occurrence)
    VALUES (%(schedule_id)s, %(occurrence)s)
    ON CONFLICT (schedule_id, occurrence) DO UPDATE SET restored_at = NULL
    RETURNING id, schedule_id, occurrence, created_at, restored_at
"""
"""Cancel one occurrence. Re-skipping an already-restored occurrence clears
the restoration, so it goes back to cancelled rather than erroring."""

RESTORE_SCHEDULE_SKIP = """
    UPDATE noc.schedule_skips
       SET restored_at = now()
     WHERE schedule_id = %(schedule_id)s
       AND occurrence  = %(occurrence)s
       AND restored_at IS NULL
    RETURNING id, schedule_id, occurrence, created_at, restored_at
"""
"""Undo a skip. Returns nothing if the occurrence was never skipped, or was
already restored."""

SELECT_EXTRA_RUNS_IN_RANGE = """
    SELECT er.id, er.application_id, er.run_at, er.created_at, er.fired_at,
           a.name AS application_name
    FROM noc.schedule_extra_runs er
    JOIN noc.applications a ON a.id = er.application_id
    WHERE er.run_at >= %(start)s AND er.run_at < %(end)s
    ORDER BY er.run_at
"""
"""List one-off extra runs due within a range, fired or not."""

SELECT_DUE_EXTRA_RUNS = """
    SELECT id, application_id, run_at, created_at, fired_at
    FROM noc.schedule_extra_runs
    WHERE fired_at IS NULL AND run_at <= %(now)s
    ORDER BY run_at
"""
"""List unfired extra runs whose time has arrived — what a tick enqueues."""

INSERT_EXTRA_RUN = """
    INSERT INTO noc.schedule_extra_runs (application_id, run_at)
    VALUES (%(application_id)s, %(run_at)s)
    RETURNING id, application_id, run_at, created_at, fired_at
"""
"""Create a one-off scheduled run. Does not touch the application's
recurring schedule."""

MARK_EXTRA_RUN_FIRED = """
    UPDATE noc.schedule_extra_runs SET fired_at = now()
     WHERE id = %(extra_run_id)s AND fired_at IS NULL
    RETURNING id, application_id, run_at, created_at, fired_at
"""
"""Mark an extra run enqueued. Guarded by `fired_at IS NULL` so a tick that
races another cannot mark — or re-enqueue — the same one twice; the actual
double-fire protection is still the idempotency key, this just keeps the
extra-runs table's own bookkeeping honest."""

DELETE_PENDING_EXTRA_RUN = """
    DELETE FROM noc.schedule_extra_runs WHERE id = %(extra_run_id)s AND fired_at IS NULL
"""
"""Remove a one-off run before it fires. A fired run cannot be deleted —
it already happened."""

SELECT_RECENT_SCHEDULED_RUNS = (
    RUN_PROJECTION
    + """
    WHERE r.trigger_source = 'schedule'
    ORDER BY r.started_at DESC
    LIMIT %(limit)s
"""
)
"""List the most recent scheduler-originated runs — both recurring
occurrences and one-off extras, distinguished by the `schedule:` / `extra:`
prefix on `idempotency_key` rather than by a separate column."""


# ===========================================================================
# Composition helpers
# ===========================================================================
def build_run_list_query(sort: str, direction: str) -> str:
    """Compose the paged run list query.

    Both arguments resolve through whitelists, so the only values that can reach
    the SQL text are identifiers this module defines. A tie-break on ``r.id``
    keeps pagination stable when two runs share a timestamp.

    Args:
        sort: Sort key, a key of :data:`~utils.constants.SORTABLE_RUN_COLUMNS`.
        direction: Direction, a key of :data:`~utils.constants.SORT_DIRECTIONS`.

    Returns:
        The complete statement, expecting the shared filter parameters plus
        ``limit`` and ``offset``.

    Raises:
        KeyError: If either argument is outside its whitelist, which indicates
            the validation layer was bypassed.
    """
    column = SORTABLE_RUN_COLUMNS[sort]
    order = SORT_DIRECTIONS[direction]
    return (
        RUN_PROJECTION
        + RUN_FILTER
        + f" ORDER BY r.{column} {order} NULLS LAST, r.id {order}"
        + " LIMIT %(limit)s OFFSET %(offset)s"
    )


def build_export_query() -> str:
    """Compose the unpaged run query used by the streaming CSV export.

    Returns:
        The complete statement, expecting the shared filter parameters. No limit
        is applied, so it must be executed through a server-side cursor.
    """
    return RUN_PROJECTION + RUN_FILTER + " ORDER BY r.started_at DESC"


def build_volume_query() -> str:
    """Compose the run-volume time series, with no gaps.

    A plain ``GROUP BY`` only returns buckets that contain runs, so a quiet
    period simply vanishes from the chart and the axis silently compresses —
    three runs spread over a week render as three adjacent bars, which reads as
    three consecutive days. Generating the full series and left-joining the
    counts keeps every interval present, including the empty ones.

    ``date_bin`` is used rather than ``date_trunc`` because the step may be five
    minutes, which ``date_trunc`` cannot express. Both the series and the
    aggregate bin against the same epoch origin, so their boundaries line up and
    the join matches.

    The step arrives as a bound parameter, so nothing is interpolated into the
    statement.

    Returns:
        The complete statement, expecting the shared filter parameters plus
        ``step``.
    """
    return (
        """
        WITH bounds AS (
          SELECT date_bin(%(step)s::interval, %(date_from)s::timestamptz, 'epoch') AS first_bucket,
                 date_bin(%(step)s::interval, %(date_to)s::timestamptz,   'epoch') AS last_bucket
        ),
        series AS (
          SELECT generate_series(first_bucket, last_bucket, %(step)s::interval) AS bucket_start
          FROM bounds
        ),
        counted AS (
          SELECT date_bin(%(step)s::interval, r.started_at, 'epoch') AS bucket_start,
                 count(*) FILTER (WHERE r.status = 'passed') AS passed,
                 count(*) FILTER (WHERE r.status = 'failed') AS failed
          FROM noc.test_runs r
        """
        + RUN_FILTER
        + """
          GROUP BY 1
        )
        SELECT s.bucket_start,
               COALESCE(c.passed, 0) AS passed,
               COALESCE(c.failed, 0) AS failed
        FROM series s
        LEFT JOIN counted c ON c.bucket_start = s.bucket_start
        ORDER BY s.bucket_start
        """
    )


def build_failures_by_dimension_query(column: str) -> str:
    """Compose a failure-breakdown query grouped by one dimension.

    Args:
        column: Column to group by. Must be a value of
            :data:`~utils.constants.FAILURE_DIMENSIONS`, never a request value,
            since it is interpolated into the statement.

    Returns:
        The complete statement, expecting the shared filter parameters.
    """
    return (
        f"SELECT r.{column} AS name, count(*) AS count"
        " FROM noc.test_runs r"
        + RUN_FILTER
        + f" AND r.status = 'failed' AND r.{column} IS NOT NULL"
        " GROUP BY 1 ORDER BY count DESC LIMIT 12"
    )
