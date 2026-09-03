import { useEffect, useMemo, useRef, useState } from 'react';
import { useAtomValue } from 'jotai';
import { runtimeByRunIdAtom } from '@/atoms/runtimeAtom';
import type { ScheduledOccurrence } from '@/types/schedule.types';
import type { TestDisplayStatus, TestRun } from '@/types/run.types';

const CLOCK_TICK_MS = 1_000;
const RECENT_RUNS_POLL_MS = 3_000;
const REMOVE_AFTER_MS = 3_000;

const TERMINAL_STATUSES: TestDisplayStatus[] = ['passed', 'failed', 'cancelled', 'timed_out'];
const isTerminal = (status: TestDisplayStatus): boolean => TERMINAL_STATUSES.includes(status);

/** Identifies one occurrence row entry across schedule/extra kinds. */
export const occurrenceKey = (occurrence: ScheduledOccurrence): string =>
  `${occurrence.kind}:${occurrence.scheduleId ?? occurrence.extraRunId}:${occurrence.occurrenceAt}`;

interface OccurrenceGroup {
  occurrenceAt: string;
  items: ScheduledOccurrence[];
}

/**
 * Live per-system status for the 24h occurrence list, plus 3s-delayed
 * removal once a row's systems have all finished.
 *
 * A run is never stored against its occurrence directly — it's matched by
 * `(applicationId, scheduledOccurrenceAt)` against the already-fetched
 * `recentRuns` list, and its live status read from `runtimeByRunIdAtom`
 * (kept current by the app-wide SSE connection in `useLiveRuns`). Before the
 * scheduler's tick has actually created the run row (up to ~60s after the
 * occurrence's time), an arrived occurrence with no match shows the same
 * `queued` placeholder a freshly-created run would have anyway, so there is
 * no visible transition once the real row appears.
 */
export function useOccurrenceRunStatuses(
  occurrenceGroups: OccurrenceGroup[],
  recentRuns: TestRun[],
  reloadRecentRuns: () => void,
): { statusByKey: Map<string, TestDisplayStatus>; hiddenOccurrenceAts: Set<string> } {
  const [now, setNow] = useState(() => Date.now());
  const [hiddenOccurrenceAts, setHiddenOccurrenceAts] = useState<Set<string>>(new Set());
  const removalTimersRef = useRef<Map<string, number>>(new Map());
  const runtimeByRunId = useAtomValue(runtimeByRunIdAtom);

  // Read fresh inside the poll interval below, instead of being dependencies
  // of it — occurrenceGroups/hiddenOccurrenceAts change far less often than
  // every render, but statusByKey is rebuilt on every 1s clock tick, and
  // depending on it there would tear the interval down before its own delay
  // ever elapsed.
  const occurrenceGroupsRef = useRef(occurrenceGroups);
  occurrenceGroupsRef.current = occurrenceGroups;
  const hiddenOccurrenceAtsRef = useRef(hiddenOccurrenceAts);
  hiddenOccurrenceAtsRef.current = hiddenOccurrenceAts;

  useEffect(() => {
    const interval = window.setInterval(() => setNow(Date.now()), CLOCK_TICK_MS);
    return () => window.clearInterval(interval);
  }, []);

  const statusByKey = useMemo(() => {
    const map = new Map<string, TestDisplayStatus>();

    for (const group of occurrenceGroups) {
      if (new Date(group.occurrenceAt).getTime() > now) continue;

      for (const occurrence of group.items) {
        if (occurrence.skipped) continue;

        const matchedRun = recentRuns.find(
          (run) =>
            run.applicationId === occurrence.applicationId &&
            run.scheduledOccurrenceAt !== null &&
            new Date(run.scheduledOccurrenceAt).getTime() ===
              new Date(occurrence.occurrenceAt).getTime(),
        );

        const status: TestDisplayStatus = matchedRun
          ? runtimeByRunId[matchedRun.id] ?? matchedRun.status
          : 'queued';

        map.set(occurrenceKey(occurrence), status);
      }
    }

    return map;
  }, [occurrenceGroups, recentRuns, runtimeByRunId, now]);

  const statusByKeyRef = useRef(statusByKey);
  statusByKeyRef.current = statusByKey;

  // Discovers a newly-created scheduled run (or a status change the live
  // channel missed). A single persistent interval, rather than one started
  // only while something is pending: "pending" itself depends on statusByKey,
  // which is rebuilt every second by the clock tick, so gating the interval's
  // own lifetime on it would tear it down before its 3s delay ever elapsed.
  // The check runs every tick regardless; it just no-ops when nothing needs it.
  useEffect(() => {
    const interval = window.setInterval(() => {
      const hasPending = occurrenceGroupsRef.current.some((group) => {
        if (hiddenOccurrenceAtsRef.current.has(group.occurrenceAt)) return false;
        if (new Date(group.occurrenceAt).getTime() > Date.now()) return false;
        return group.items.some((occurrence) => {
          if (occurrence.skipped) return false;
          const status = statusByKeyRef.current.get(occurrenceKey(occurrence));
          return status === undefined || !isTerminal(status);
        });
      });

      if (hasPending) reloadRecentRuns();
    }, RECENT_RUNS_POLL_MS);

    return () => window.clearInterval(interval);
  }, [reloadRecentRuns]);

  // 3s after the last non-skipped system in a row turns terminal, hide the row.
  useEffect(() => {
    for (const group of occurrenceGroups) {
      if (hiddenOccurrenceAts.has(group.occurrenceAt)) continue;
      if (removalTimersRef.current.has(group.occurrenceAt)) continue;

      const activeItems = group.items.filter((occurrence) => !occurrence.skipped);
      if (activeItems.length === 0) continue;

      const allTerminal = activeItems.every((occurrence) => {
        const status = statusByKey.get(occurrenceKey(occurrence));
        return status !== undefined && isTerminal(status);
      });
      if (!allTerminal) continue;

      const occurrenceAt = group.occurrenceAt;
      const timerId = window.setTimeout(() => {
        setHiddenOccurrenceAts((current) => new Set(current).add(occurrenceAt));
        removalTimersRef.current.delete(occurrenceAt);
      }, REMOVE_AFTER_MS);

      removalTimersRef.current.set(occurrenceAt, timerId);
    }
  }, [occurrenceGroups, statusByKey, hiddenOccurrenceAts]);

  useEffect(() => {
    const timers = removalTimersRef.current;
    return () => {
      for (const timerId of timers.values()) window.clearTimeout(timerId);
      timers.clear();
    };
  }, []);

  return { statusByKey, hiddenOccurrenceAts };
}
