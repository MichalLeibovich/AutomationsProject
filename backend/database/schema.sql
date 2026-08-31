-- ===========================================================================
-- NOC Test Management — schema
--
-- Everything lives in the `noc` schema. There are no user accounts, roles or
-- audit tables: this database stores automations and their results, nothing
-- about who is looking at them.
--
-- Idempotent — applying it repeatedly is safe and is part of the setup routine.
-- Requires PostgreSQL 14 or newer (CREATE OR REPLACE TRIGGER).
-- ===========================================================================

CREATE SCHEMA IF NOT EXISTS noc;

-- gen_random_uuid() comes from pgcrypto; citext gives case-insensitive slugs,
-- so 'Login-Flow' and 'login-flow' cannot both exist.
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS citext;
-- pg_trgm makes '%term%' searches indexable. Without it a leading wildcard
-- forces a sequential scan of every run.
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ---------------------------------------------------------------------------
-- Enums
--
-- One DO block each: a duplicate_object inside a combined block would abort
-- every type after it, leaving the schema half-created.
-- ---------------------------------------------------------------------------
DO $$ BEGIN CREATE TYPE noc.test_scope AS ENUM ('application', 'general');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN CREATE TYPE noc.test_kind AS ENUM ('main', 'secondary', 'general');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN CREATE TYPE noc.run_status AS ENUM
  ('queued', 'running', 'passed', 'failed', 'cancelled', 'timed_out');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN CREATE TYPE noc.trigger_source AS ENUM
  ('manual', 'bulk', 'schedule', 'ci', 'api');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN CREATE TYPE noc.artifact_kind AS ENUM
  ('screenshot', 'log', 'trace', 'video', 'har', 'report');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN CREATE TYPE noc.step_status AS ENUM ('passed', 'failed', 'skipped');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- ---------------------------------------------------------------------------
-- Applications
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS noc.applications (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name          text   NOT NULL UNIQUE,
  slug          citext NOT NULL UNIQUE,
  color         text   NOT NULL,
  display_order smallint NOT NULL DEFAULT 0,
  is_active     boolean  NOT NULL DEFAULT true,
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now(),

  CONSTRAINT applications_color_hex CHECK (color ~ '^#[0-9A-Fa-f]{6}$')
);

CREATE INDEX IF NOT EXISTS applications_active_order_idx
  ON noc.applications (display_order, name) WHERE is_active;

-- ---------------------------------------------------------------------------
-- Test definitions — the automation catalog
--
-- `runner_target` is the pytest node id the runner executes, for example
-- "tests/test_login.py::test_valid_login". It is what ties a database row to
-- an actual automation on disk, and is unique so a result can be matched back
-- to exactly one definition.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS noc.test_definitions (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  application_id  uuid REFERENCES noc.applications (id) ON DELETE RESTRICT,
  scope           noc.test_scope NOT NULL,
  kind            noc.test_kind  NOT NULL,
  name            text NOT NULL,
  description     text,
  runner_target   text NOT NULL UNIQUE,
  display_order   smallint NOT NULL DEFAULT 0,
  timeout_seconds integer  NOT NULL DEFAULT 600,
  is_active       boolean  NOT NULL DEFAULT true,
  archived_at     timestamptz,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now(),

  -- An application test belongs to an application; general automation does not.
  CONSTRAINT test_definitions_scope_consistent CHECK (
    (scope = 'application' AND application_id IS NOT NULL AND kind IN ('main','secondary')) OR
    (scope = 'general'     AND application_id IS NULL     AND kind = 'general')
  ),
  CONSTRAINT test_definitions_timeout_sane CHECK (timeout_seconds BETWEEN 10 AND 7200)
);

-- Exactly one active main test per application, enforced by the database so no
-- code path can create a second.
CREATE UNIQUE INDEX IF NOT EXISTS test_definitions_one_main_per_app
  ON noc.test_definitions (application_id)
  WHERE kind = 'main' AND is_active;

CREATE INDEX IF NOT EXISTS test_definitions_scope_idx
  ON noc.test_definitions (scope, application_id, display_order) WHERE is_active;

-- ---------------------------------------------------------------------------
-- Test runs
--
-- RANGE-partitioned monthly on started_at. Retention becomes a partition DROP
-- rather than a mass DELETE, which stays fast as history grows.
--
-- A partitioned table's primary key must include the partition key, hence
-- (id, started_at).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS noc.test_runs (
  id                 uuid NOT NULL DEFAULT gen_random_uuid(),
  test_definition_id uuid NOT NULL REFERENCES noc.test_definitions (id) ON DELETE RESTRICT,

  -- Denormalised and frozen at insert: renaming an application must never
  -- rewrite what history says happened.
  application_id     uuid REFERENCES noc.applications (id) ON DELETE SET NULL,
  scope              noc.test_scope NOT NULL,
  scope_label        text NOT NULL,
  test_name          text NOT NULL,
  runner_target      text NOT NULL,

  status             noc.run_status NOT NULL DEFAULT 'queued',
  queued_at          timestamptz NOT NULL DEFAULT now(),
  started_at         timestamptz NOT NULL DEFAULT now(),
  ended_at           timestamptz,
  duration_seconds   integer GENERATED ALWAYS AS (
                       CASE WHEN ended_at IS NULL THEN NULL
                       ELSE GREATEST(0, EXTRACT(EPOCH FROM (ended_at - started_at))::integer) END
                     ) STORED,

  -- Free text: a hostname, a CI job name, or 'manual'. There are no accounts.
  triggered_by       text NOT NULL DEFAULT 'manual',
  trigger_source     noc.trigger_source NOT NULL DEFAULT 'manual',

  worker_id          text,
  attempt            smallint NOT NULL DEFAULT 1,
  idempotency_key    text,
  correlation_id     uuid,

  -- feature and error_type drive the dashboard charts; reason and stack_trace
  -- are what the debrief panel shows.
  failure_feature    text,
  failure_error_type text,
  failure_reason     text,
  stack_trace        text,

  total_steps        smallint NOT NULL DEFAULT 0,
  failed_steps       smallint NOT NULL DEFAULT 0,
  artifact_count     smallint NOT NULL DEFAULT 0,

  -- Everything searchable, lowercased and concatenated, maintained by the
  -- database. Generated rather than trigger-populated because the expression is
  -- immutable, so there is no way for it to drift out of step with the row.
  search_text        text GENERATED ALWAYS AS (
                       lower(
                         coalesce(test_name, '')          || ' ' ||
                         coalesce(scope_label, '')        || ' ' ||
                         coalesce(runner_target, '')       || ' ' ||
                         coalesce(triggered_by, '')        || ' ' ||
                         coalesce(failure_reason, '')      || ' ' ||
                         coalesce(failure_feature, '')     || ' ' ||
                         coalesce(failure_error_type, '')
                       )
                     ) STORED,

  PRIMARY KEY (id, started_at),

  CONSTRAINT test_runs_ended_after_started CHECK (ended_at IS NULL OR ended_at >= started_at),
  -- A failure with no reason is unusable to whoever reads it next.
  CONSTRAINT test_runs_failure_has_reason CHECK (
    status <> 'failed' OR failure_reason IS NOT NULL
  )
) PARTITION BY RANGE (started_at);

CREATE INDEX IF NOT EXISTS test_runs_started_idx    ON noc.test_runs (started_at DESC);
CREATE INDEX IF NOT EXISTS test_runs_status_idx     ON noc.test_runs (status, started_at DESC);
CREATE INDEX IF NOT EXISTS test_runs_definition_idx ON noc.test_runs (test_definition_id, started_at DESC);
CREATE INDEX IF NOT EXISTS test_runs_scope_idx      ON noc.test_runs (scope, application_id, started_at DESC);


-- ---------------------------------------------------------------------------
-- Upgrade path for databases created before substring search
--
-- CREATE TABLE IF NOT EXISTS does nothing to an existing table, so an installed
-- database needs these explicitly. All are no-ops on a fresh one.
-- ---------------------------------------------------------------------------
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'noc' AND table_name = 'test_runs' AND column_name = 'search_text'
  ) THEN
    ALTER TABLE noc.test_runs ADD COLUMN search_text text
      GENERATED ALWAYS AS (
        lower(
          coalesce(test_name, '')          || ' ' ||
          coalesce(scope_label, '')        || ' ' ||
          coalesce(runner_target, '')       || ' ' ||
          coalesce(triggered_by, '')        || ' ' ||
          coalesce(failure_reason, '')      || ' ' ||
          coalesce(failure_feature, '')     || ' ' ||
          coalesce(failure_error_type, '')
        )
      ) STORED;
  END IF;
END $$;

DROP TRIGGER IF EXISTS test_runs_search_update ON noc.test_runs;
DROP FUNCTION IF EXISTS noc.test_runs_search_trigger();
ALTER TABLE noc.test_runs DROP COLUMN IF EXISTS search_document;

-- Created after the column exists: on an already-installed database the
-- column is added by the block above, so indexing it earlier would fail.
CREATE INDEX IF NOT EXISTS test_runs_search_idx
  ON noc.test_runs USING gin (search_text gin_trgm_ops);

-- ---------------------------------------------------------------------------
-- Partition management
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION noc.ensure_run_partition(target date)
RETURNS text LANGUAGE plpgsql AS $$
DECLARE
  start_of_month date := date_trunc('month', target)::date;
  end_of_month   date := (date_trunc('month', target) + interval '1 month')::date;
  partition_name text := 'test_runs_' || to_char(start_of_month, 'YYYY_MM');
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'noc' AND c.relname = partition_name
  ) THEN
    EXECUTE format(
      'CREATE TABLE noc.%I PARTITION OF noc.test_runs FOR VALUES FROM (%L) TO (%L)',
      partition_name, start_of_month, end_of_month
    );
  END IF;
  RETURN partition_name;
END $$;

CREATE OR REPLACE FUNCTION noc.drop_run_partitions_before(cutoff date)
RETURNS integer LANGUAGE plpgsql AS $$
DECLARE
  rec     record;
  removed integer := 0;
BEGIN
  FOR rec IN
    SELECT c.relname FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'noc'
      AND c.relname LIKE 'test_runs_%'
      AND to_date(right(c.relname, 7), 'YYYY_MM') < date_trunc('month', cutoff)
  LOOP
    EXECUTE format('DROP TABLE IF EXISTS noc.%I', rec.relname);
    removed := removed + 1;
  END LOOP;
  RETURN removed;
END $$;

-- ---------------------------------------------------------------------------
-- Run steps — per-step detail of one automation run
--
-- Carries run_started_at because a foreign key into a partitioned table must
-- include its partition key.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS noc.run_steps (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id         uuid NOT NULL,
  run_started_at timestamptz NOT NULL,

  step_index     smallint NOT NULL,
  name           text NOT NULL,
  status         noc.step_status NOT NULL,
  duration_ms    integer NOT NULL DEFAULT 0,
  error_message  text,
  started_at     timestamptz NOT NULL DEFAULT now(),

  FOREIGN KEY (run_id, run_started_at)
    REFERENCES noc.test_runs (id, started_at) ON DELETE CASCADE,

  CONSTRAINT run_steps_duration_positive CHECK (duration_ms >= 0),
  CONSTRAINT run_steps_unique_index UNIQUE (run_id, step_index)
);

CREATE INDEX IF NOT EXISTS run_steps_run_idx ON noc.run_steps (run_id, step_index);

-- ---------------------------------------------------------------------------
-- Run artifacts
--
-- `local_path` covers a runner writing to a shared folder; the s3 columns cover
-- object storage. Either is acceptable, neither being present is not.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS noc.run_artifacts (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id         uuid NOT NULL,
  run_started_at timestamptz NOT NULL,

  kind           noc.artifact_kind NOT NULL,
  file_name      text NOT NULL,
  local_path     text,
  s3_bucket      text,
  s3_key         text,
  content_type   text NOT NULL DEFAULT 'application/octet-stream',
  size_bytes     bigint NOT NULL DEFAULT 0,
  created_at     timestamptz NOT NULL DEFAULT now(),

  FOREIGN KEY (run_id, run_started_at)
    REFERENCES noc.test_runs (id, started_at) ON DELETE CASCADE,

  CONSTRAINT run_artifacts_has_location CHECK (local_path IS NOT NULL OR s3_key IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS run_artifacts_run_idx ON noc.run_artifacts (run_id, kind);

-- ---------------------------------------------------------------------------
-- Run comments — free-text operator notes, author is a plain name
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS noc.run_comments (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id         uuid NOT NULL,
  run_started_at timestamptz NOT NULL,

  author_name    text NOT NULL,
  body           text NOT NULL,
  created_at     timestamptz NOT NULL DEFAULT now(),
  deleted_at     timestamptz,

  FOREIGN KEY (run_id, run_started_at)
    REFERENCES noc.test_runs (id, started_at) ON DELETE CASCADE,

  CONSTRAINT run_comments_body_not_blank CHECK (length(btrim(body)) > 0)
);

CREATE INDEX IF NOT EXISTS run_comments_run_idx
  ON noc.run_comments (run_id, created_at) WHERE deleted_at IS NULL;

-- ---------------------------------------------------------------------------
-- Idempotency claims
--
-- Deliberately NOT partitioned. A unique index on a partitioned table must
-- include the partition key, and started_at differs between two retries — so an
-- ON CONFLICT there would never fire and the same run could be enqueued twice.
-- Here the key is a genuine single-column primary key.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS noc.run_idempotency (
  idempotency_key text PRIMARY KEY,
  run_id          uuid NOT NULL,
  run_started_at  timestamptz NOT NULL,
  created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS run_idempotency_created_idx ON noc.run_idempotency (created_at);

CREATE OR REPLACE FUNCTION noc.prune_idempotency_claims(retain interval DEFAULT '7 days')
RETURNS integer LANGUAGE plpgsql AS $$
DECLARE removed integer;
BEGIN
  DELETE FROM noc.run_idempotency WHERE created_at < now() - retain;
  GET DIAGNOSTICS removed = ROW_COUNT;
  RETURN removed;
END $$;

-- ---------------------------------------------------------------------------
-- Schedules — recurring automation firing rules
--
-- Occurrences are never stored: they are computed on demand from
-- (every_hours, anchor_minute, timezone) by the application layer
-- (utils/schedule_time.py), so this table only ever holds one row per
-- application per cadence, however far into the future "upcoming" looks.
--
-- Bound to application_id rather than a frozen test_definition_id, so a
-- schedule keeps firing the application's *current* main test even if that
-- test is later renamed (which archives the old definition row and creates a
-- new one) — the same resolution bulk-run already does.
-- ---------------------------------------------------------------------------
-- One schedule per application today — the interface offers no way to
-- attach a second cadence to the same application, so the unique constraint
-- keeps re-seeding idempotent (upsert on application_id) rather than
-- accumulating duplicate rows.
CREATE TABLE IF NOT EXISTS noc.schedules (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  application_id uuid NOT NULL UNIQUE REFERENCES noc.applications (id) ON DELETE CASCADE,
  every_hours    smallint NOT NULL,
  anchor_minute  smallint NOT NULL DEFAULT 0,
  timezone       text NOT NULL DEFAULT 'Asia/Jerusalem',
  is_active      boolean NOT NULL DEFAULT true,
  created_at     timestamptz NOT NULL DEFAULT now(),

  CONSTRAINT schedules_every_hours_positive CHECK (every_hours > 0 AND every_hours <= 24),
  CONSTRAINT schedules_every_hours_divides_day CHECK (24 % every_hours = 0),
  CONSTRAINT schedules_anchor_minute_range CHECK (anchor_minute BETWEEN 0 AND 59)
);

-- ---------------------------------------------------------------------------
-- Schedule skips — one cancelled recurring occurrence
--
-- Deleting "the 02:00 run" cannot delete a row that does not exist yet, since
-- occurrences are computed rather than stored. A skip is what makes an
-- occurrence not fire. `restored_at` is how undo works: the row is kept and
-- greyed out rather than removed, so a deliberate gap is visibly a deliberate
-- gap rather than looking like a bug.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS noc.schedule_skips (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  schedule_id uuid NOT NULL REFERENCES noc.schedules (id) ON DELETE CASCADE,
  occurrence  timestamptz NOT NULL,
  created_at  timestamptz NOT NULL DEFAULT now(),
  restored_at timestamptz,

  UNIQUE (schedule_id, occurrence)
);

CREATE INDEX IF NOT EXISTS schedule_skips_active_idx
  ON noc.schedule_skips (schedule_id, occurrence) WHERE restored_at IS NULL;

-- ---------------------------------------------------------------------------
-- Schedule extra runs — one-off scheduled runs outside any recurring rule
--
-- What the "+" control creates: a single run for one application at a chosen
-- time, entirely independent of that application's recurring schedule (which
-- is left untouched). `fired_at` is set once the tick has enqueued it, which
-- is also what stops it from being deleted after the fact — a run that
-- already happened cannot be un-scheduled.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS noc.schedule_extra_runs (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  application_id uuid NOT NULL REFERENCES noc.applications (id) ON DELETE CASCADE,
  run_at         timestamptz NOT NULL,
  created_at     timestamptz NOT NULL DEFAULT now(),
  fired_at       timestamptz
);

CREATE INDEX IF NOT EXISTS schedule_extra_runs_pending_idx
  ON noc.schedule_extra_runs (run_at) WHERE fired_at IS NULL;

-- ---------------------------------------------------------------------------
-- Daily rollup
--
-- `application_key` is materialised as a column so the unique index can be
-- built on plain columns: PostgreSQL requires that for a CONCURRENTLY refresh
-- and rejects an index built on an expression.
-- ---------------------------------------------------------------------------
CREATE MATERIALIZED VIEW IF NOT EXISTS noc.mv_daily_run_stats AS
SELECT
  date_trunc('day', started_at)::date AS day,
  scope,
  application_id,
  COALESCE(application_id, '00000000-0000-0000-0000-000000000000'::uuid) AS application_key,
  scope_label,
  count(*)                                  AS total_runs,
  count(*) FILTER (WHERE status = 'passed') AS passed_runs,
  count(*) FILTER (WHERE status = 'failed') AS failed_runs,
  avg(duration_seconds) FILTER (WHERE duration_seconds IS NOT NULL) AS avg_duration_seconds
FROM noc.test_runs
GROUP BY 1, 2, 3, 4, 5
WITH NO DATA;

CREATE UNIQUE INDEX IF NOT EXISTS mv_daily_run_stats_key
  ON noc.mv_daily_run_stats (day, scope, application_key, scope_label);

-- Picks the refresh mode itself: CONCURRENTLY needs the view already populated
-- (it is created WITH NO DATA) and a unique index with no WHERE clause. Failing
-- either raises at refresh time rather than at definition time.
CREATE OR REPLACE FUNCTION noc.refresh_daily_run_stats()
RETURNS text LANGUAGE plpgsql AS $$
DECLARE can_concurrent boolean;
BEGIN
  SELECT c.relispopulated
         AND EXISTS (SELECT 1 FROM pg_index i
                     WHERE i.indrelid = c.oid AND i.indisunique AND i.indpred IS NULL)
    INTO can_concurrent
  FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
  WHERE n.nspname = 'noc' AND c.relname = 'mv_daily_run_stats';

  IF can_concurrent THEN
    REFRESH MATERIALIZED VIEW CONCURRENTLY noc.mv_daily_run_stats;
    RETURN 'concurrent';
  END IF;

  REFRESH MATERIALIZED VIEW noc.mv_daily_run_stats;
  RETURN 'blocking';
END $$;

-- ---------------------------------------------------------------------------
-- updated_at maintenance
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION noc.touch_updated_at()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN NEW.updated_at := now(); RETURN NEW; END $$;

CREATE OR REPLACE TRIGGER applications_touch
  BEFORE UPDATE ON noc.applications
  FOR EACH ROW EXECUTE FUNCTION noc.touch_updated_at();

CREATE OR REPLACE TRIGGER test_definitions_touch
  BEFORE UPDATE ON noc.test_definitions
  FOR EACH ROW EXECUTE FUNCTION noc.touch_updated_at();

-- Provision the current month so the first insert has somewhere to land.
SELECT noc.ensure_run_partition(CURRENT_DATE);
