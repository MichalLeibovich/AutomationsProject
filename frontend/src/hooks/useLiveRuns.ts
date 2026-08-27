import { useEffect, useRef } from 'react';
import { useSetAtom } from 'jotai';
import { applyLiveUpdateAtom } from '@/atoms/runtimeAtom';
import { endpoints } from '@/api/endpoints';
import type { LiveRunUpdate } from '@/types/run.types';

const RECONNECT_BASE_MS = 1_000;
const RECONNECT_MAX_MS = 30_000;

const BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? '/api';

/**
 * Subscribes to server-sent run status.
 *
 * Elapsed time is server-authoritative: a local interval would drift, and
 * would report the wrong value after a backgrounded tab is restored.
 *
 * EventSource is used rather than Axios because it handles the streaming
 * framing natively; Axios has no equivalent for server-sent events.
 */
export function useLiveRuns(enabled = true): void {
  const applyUpdate = useSetAtom(applyLiveUpdateAtom);
  const attemptRef = useRef(0);

  useEffect(() => {
    if (!enabled) return;

    let source: EventSource | null = null;
    let reconnectTimer: number | undefined;
    let disposed = false;

    const connect = () => {
      source = new EventSource(`${BASE_URL}${endpoints.runs.stream}`, {
        withCredentials: true,
      });

      source.onopen = () => {
        attemptRef.current = 0;
      };

      source.onmessage = (event: MessageEvent<string>) => {
        try {
          const payload = JSON.parse(event.data) as LiveRunUpdate;
          applyUpdate({
            definitionId: payload.testDefinitionId,
            runId: payload.runId,
            status: payload.status,
            elapsedSeconds: payload.elapsedSeconds,
            durationSeconds: payload.durationSeconds,
            failureReason: payload.failureReason,
          });
        } catch {
          // A malformed frame must not tear down the stream.
        }
      };

      source.onerror = () => {
        source?.close();
        if (disposed) return;
        // Exponential backoff, so a backend restart does not become a
        // reconnect storm from every open tab.
        const delay = Math.min(RECONNECT_BASE_MS * 2 ** attemptRef.current++, RECONNECT_MAX_MS);
        reconnectTimer = window.setTimeout(connect, delay);
      };
    };

    connect();

    return () => {
      disposed = true;
      source?.close();
      if (reconnectTimer) window.clearTimeout(reconnectTimer);
    };
  }, [enabled, applyUpdate]);
}
