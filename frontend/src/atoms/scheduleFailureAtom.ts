import { atom } from 'jotai';

/** One scheduled automation's failure, as observed live on the SSE stream. */
export interface ScheduleFailureEvent {
  runId: string;
  scopeLabel: string;
  testName: string;
}

/**
 * The most recently observed scheduled-run failure, written by useLiveRuns
 * the moment it sees one on the stream (edge-triggered — a run already
 * settled into "failed" before this tab connected does not re-fire it).
 *
 * A dedicated atom rather than folding this into runtimeByDefinitionAtom:
 * that atom exists to drive the test grid's display and every consumer there
 * would otherwise need to ignore three fields it has no use for. This one
 * exists solely for useScheduleFailureNotifications to react to.
 */
export const scheduleFailureEventAtom = atom<ScheduleFailureEvent | null>(null);
