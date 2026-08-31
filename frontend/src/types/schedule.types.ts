/** Scheduled-automation types: recurring schedules, occurrences, extras. */

import type { RunStatus } from './run.types';

/** A recurring automation firing rule. */
export interface Schedule {
  id: string;
  applicationId: string;
  applicationName: string | null;
  /** Interval between occurrences, in hours. */
  everyHours: number;
  /** Minute past each hour the schedule fires on. */
  anchorMinute: number;
  /** IANA zone the rule is defined against, e.g. "Asia/Jerusalem". */
  timezone: string;
  isActive: boolean;
}

/**
 * One entry in the upcoming/24h schedule view — a recurring occurrence or a
 * one-off extra run, computed on demand rather than stored.
 */
export interface ScheduledOccurrence {
  kind: 'schedule' | 'extra';
  occurrenceAt: string;
  applicationId: string;
  applicationName: string;
  /** Set when `kind === 'schedule'`. */
  scheduleId: string | null;
  /** Set when `kind === 'extra'`. */
  extraRunId: string | null;
  /** Cancelled but still listed — the interface greys it out with a restore
   * action rather than hiding it, so a deliberate gap does not look like a
   * bug. Always false for an extra run: those are deleted outright. */
  skipped: boolean;
}

/** A one-off scheduled run outside any recurring rule. */
export interface ScheduleExtraRun {
  id: string;
  applicationId: string;
  applicationName: string | null;
  runAt: string;
  createdAt: string;
  /** Set once the scheduler has enqueued it. */
  firedAt: string | null;
}

/** One application's outcome within a grouped scheduled-run slot. */
export interface ScheduledRunEntry {
  applicationId: string;
  applicationName: string;
  runId: string;
  status: RunStatus;
}

/**
 * Every scheduled run that shares one occurrence slot — several applications
 * on the same cadence land under one group even though their individual runs
 * were created a few seconds or minutes apart.
 */
export interface ScheduledRunGroup {
  occurrenceAt: string;
  entries: ScheduledRunEntry[];
}
