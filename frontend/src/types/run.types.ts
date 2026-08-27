/** Run, step, comment and artifact types. */

/**
 * A run's persisted state.
 *
 * `queued` and `running` are in flight; the rest are terminal. A cancelled run is
 * recorded as cancelled, never as a pass.
 */
export type RunStatus =
  | 'queued'
  | 'running'
  | 'passed'
  | 'failed'
  | 'cancelled'
  | 'timed_out';

/**
 * A status as the interface presents it.
 *
 * Adds `idle` for an automation that has never run. The API has no row for that
 * case, but the grid still needs to render it.
 */
export type TestDisplayStatus = RunStatus | 'idle';

/** How a run was triggered. */
export type TriggerSource = 'manual' | 'bulk' | 'schedule' | 'ci' | 'api';

/** Why a run failed. */
export interface RunFailure {
  /** Component that failed, driving the failures-by-feature chart. */
  feature: string | null;
  /** Failure category, driving the error-type breakdown. */
  errorType: string | null;
  /** Human-readable explanation shown in the debrief. */
  reason: string;
  /** Full traceback, when the runner captured one. */
  stackTrace: string | null;
}

/** One execution of an automation. */
export interface TestRun {
  id: string;
  testDefinitionId: string;
  /** Automation name, frozen when the run was created. */
  testName: string;
  /** The pytest node id that was executed, frozen at creation. */
  runnerTarget: string;
  applicationId: string | null;
  scope: 'application' | 'general';
  /**
   * Application name, or the general label, frozen at creation.
   *
   * Stored rather than resolved at read time, so renaming an application never
   * rewrites run history.
   */
  scopeLabel: string;
  status: RunStatus;
  queuedAt: string | null;
  startedAt: string;
  /** Null while the run is in flight. */
  endedAt: string | null;
  /** Computed by the database on completion. Null while in flight. */
  durationSeconds: number | null;
  /** Free text — a hostname, a CI job name, or `manual`. There are no accounts. */
  triggeredBy: string;
  triggerSource: TriggerSource;
  /** Identifier of the worker that executed it, when one reported. */
  workerId: string | null;
  attempt: number;
  /** Steps the runner reported. Zero when it reported none. */
  totalSteps: number;
  failedSteps: number;
  artifactCount: number;
  /** Null unless the run failed. */
  failure: RunFailure | null;
}

/** Status of one step within a run. */
export type StepStatus = 'passed' | 'failed' | 'skipped';

/**
 * One step of an automation run.
 *
 * Steps are what turn a bare pass or fail into something diagnosable: which part
 * broke, how long each part took, and what the error was.
 */
export interface RunStep {
  id: string;
  runId: string;
  /** Zero-based position within the run. */
  index: number;
  name: string;
  status: StepStatus;
  durationMs: number;
  errorMessage: string | null;
  startedAt: string;
}

/**
 * A live status frame from the server-sent event stream.
 *
 * Elapsed time is computed server-side, so every client agrees regardless of
 * clock skew and a backgrounded tab is correct the moment it returns.
 */
export interface LiveRunUpdate {
  runId: string;
  testDefinitionId: string;
  status: RunStatus;
  elapsedSeconds: number;
  durationSeconds: number | null;
  failureReason: string | null;
}

/** A free-text operator note attached to a run. */
export interface RunComment {
  id: string;
  runId: string;
  /** Author name as typed; there are no accounts. */
  authorName: string;
  body: string;
  createdAt: string;
}

/** A file produced by a run. */
export interface RunArtifact {
  id: string;
  runId: string;
  kind: 'screenshot' | 'log' | 'trace' | 'video' | 'har' | 'report';
  fileName: string;
  contentType: string;
  sizeBytes: number;
  /** API download path, or null when the file has no reachable location. */
  downloadUrl: string | null;
}
