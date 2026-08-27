import { atom } from 'jotai';
import type { RunStatus, TestDisplayStatus } from '@/types/run.types';

/**
 * Ephemeral, in-flight state for a test definition in the current session.
 * Server-owned history is fetched per view; only live status lives here.
 */
export interface TestRuntimeState {
  definitionId: string;
  runId: string | null;
  status: TestDisplayStatus;
  elapsedSeconds: number;
  endedAt: string | null;
  durationSeconds: number | null;
  failureReason: string | null;
}

export const runtimeByDefinitionAtom = atom<Record<string, TestRuntimeState>>({});

export const hasActiveRunsAtom = atom((get) =>
  Object.values(get(runtimeByDefinitionAtom)).some(
    (state) => state.status === 'running' || state.status === 'queued',
  ),
);

/**
 * Applied optimistically the moment a run is submitted, then reconciled by the
 * live channel.
 *
 * The optimistic status is `queued`, not `running`, because that is what the API
 * actually created. Claiming it is running would be a guess about a worker that
 * may not even be listening — and it read as a visible glitch: the row showed
 * running, the live channel corrected it to queued, then the worker moved it to
 * running. A run cannot execute before it is queued, so it should never be shown
 * that way.
 */
export const markRunStartedAtom = atom(
  null,
  (get, set, payload: { definitionId: string; runId: string }) => {
    set(runtimeByDefinitionAtom, {
      ...get(runtimeByDefinitionAtom),
      [payload.definitionId]: {
        definitionId: payload.definitionId,
        runId: payload.runId,
        status: 'queued',
        elapsedSeconds: 0,
        endedAt: null,
        durationSeconds: null,
        failureReason: null,
      },
    });
  },
);

export const applyLiveUpdateAtom = atom(
  null,
  (
    get,
    set,
    payload: {
      definitionId: string;
      runId: string;
      status: RunStatus;
      elapsedSeconds: number;
      durationSeconds?: number | null;
      failureReason?: string | null;
    },
  ) => {
    const isActive = payload.status === 'running' || payload.status === 'queued';
    set(runtimeByDefinitionAtom, {
      ...get(runtimeByDefinitionAtom),
      [payload.definitionId]: {
        definitionId: payload.definitionId,
        runId: payload.runId,
        status: payload.status,
        elapsedSeconds: payload.elapsedSeconds,
        endedAt: isActive ? null : new Date().toISOString(),
        durationSeconds: payload.durationSeconds ?? null,
        failureReason: payload.failureReason ?? null,
      },
    });
  },
);

export const resetRuntimeAtom = atom(null, (_get, set) => {
  set(runtimeByDefinitionAtom, {});
});
